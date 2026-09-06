from typing import Dict, Any, TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pathlib import Path
from src.core.tools import verify_prescription
from src.utils.model_loader import ModelLoader
from src.utils.file_io import gather_files, build_content_block
from src.core.prompts.prompts_factory import prompt_registry
from litellm import completion
from langchain.chat_models import init_chat_model 
from langgraph.graph import add_messages

ml = ModelLoader()
tools = [verify_prescription]


class PrescriptionAgent(TypedDict):
    upload_img_path: Annotated[str, "Path to the uploaded prescription image"]
    disease_name: Annotated[str, "Name of the disease for which the prescription is intended"]
    sub_agent_response: Annotated[str, "Response from the sub-agent processing the prescription"]
    agent_response: Annotated[str, "Response from the main agent after processing the prescription"]
    verified: Annotated[bool, "Indicates whether the prescription has been verified or not"]
    messages: Annotated[List[BaseMessage], add_messages]  # Typed with BaseMessage for clarity

class AgentHub:
    def __init__(self):
        self.coordinator_system_prompt = prompt_registry["coordinator"][0]
        self.coordinator_user_prompt = prompt_registry["coordinator"][1]
        self.sub_agent_system_prompt = prompt_registry["subagent"][0]
        self.sub_agent_user_prompt = prompt_registry["subagent"][1]
        self.sub_agent_brain_details = ml.load_llm("Anthropic")
        self.coordinator_agent_brain_details = ml.load_llm("groq")
        self.c_llm = init_chat_model(model=self.coordinator_agent_brain_details[1], api_key=self.coordinator_agent_brain_details[0])
        self.binded_llm = self.c_llm.bind_tools(tools)
        
    def coordinator_agent(self, state: PrescriptionAgent) -> Dict[str, Any]:
        history = state.get("messages") or []
        new_messages = []
        
        # 1. Build initial context messages ONLY if history is empty
        if not history:
            initial_context = [
                SystemMessage(content=self.coordinator_system_prompt),
                HumanMessage(content=self.coordinator_user_prompt.format(
                    ocr_markdown_output=state["sub_agent_response"],
                    patient_reported_condition=state["disease_name"] or "Not provided"
                ))
            ]
            new_messages.extend(initial_context)
            # Combine temporarily just for the LLM invocation input
            invocation_history = initial_context
        else:
            invocation_history = history

        # 2. Invoke model passing the full history
        res = self.binded_llm.invoke(invocation_history)
        new_messages.append(res)
        
        # 3. Determine flags safely
        has_tool_calls = bool(getattr(res, "tool_calls", None))
        agent_response = res.content if not has_tool_calls else "Invoking verification tools..."
        
        # 4. Return ONLY the new messages so LangGraph can append them cleanly
        return {
            "messages": new_messages, 
            "agent_response": agent_response, 
            "verified": not has_tool_calls
        }  
          
    def sub_agent(self, state: PrescriptionAgent) -> Dict[str, Any]:
        img_paths = gather_files(Path(state["upload_img_path"]))
        content_block = build_content_block(img_paths[0])
        disease = state.get("disease_name", "") or ""
        context_note = f"\n\nPatient-reported condition (context only): {disease}" if disease else ""
        response = completion(
            model=self.sub_agent_brain_details[1],
            api_key=self.sub_agent_brain_details[0],
            messages=[
                {"role": "system", "content": self.sub_agent_system_prompt},
                {"role": "user", "content": [content_block, {"type": "text", "text": self.sub_agent_user_prompt + context_note}]}
            ],
            max_completion_tokens=4096
        )
        return {"sub_agent_response": response.choices[0].message.content}
