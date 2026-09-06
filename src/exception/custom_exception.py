import sys 

def detailed_exception_message(error_message, error_detail:sys):
    _,_,exc_tb = error_detail.exc_info()
    filename = exc_tb.tb_frame.f_code.co_filename
    line_number = exc_tb.tb_lineno
    exception_message = f"Exception occurred in file: {filename}, line: {line_number}, message: {str(error_message)}"
    return exception_message

class DocumentPortalException(Exception):
    def __init__(self,error_message, error_detail:sys):
        super().__init__(error_message)
        self.error_message = detailed_exception_message(error_message, error_detail)
    def __str__(self):
        return self.error_message
    