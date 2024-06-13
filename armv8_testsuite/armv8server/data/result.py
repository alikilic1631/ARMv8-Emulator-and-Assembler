import armv8suite.data.result as d_result
from armv8suite.data.result import ResultType

# class WResultType():
#     def __init__(self, result: ResultType):
#         self.result = result

#     def __str__(self) -> str:
#         return str(self.result)
    
def column_template(result: ResultType) -> str:
    if result is ResultType.CORRECT:
        badge_modifier = "success"
    elif result is ResultType.INCORRECT:
        badge_modifier = "warning"
    elif result is ResultType.FAILED:
        badge_modifier = "danger"
    else:
        badge_modifier = "success"

    return f'<td><span class="badge bg-{badge_modifier}">{result}</span></td>'
