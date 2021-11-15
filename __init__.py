from . import ImplicitModeller

def getMetaData():
    return {}
    # return {
    #     "tool": {
    #         "name": "Function Generator",
    #         "description": "Generates parameterized models of Gyroid and Fisher Koch S triply periodic minimal surfaces.",
    #         "tool_panel": "ImplicitModeller.qml",
    #         "weight": 2
    #     }
    # }

def register(app):
    return {"extension": ImplicitModeller.ImplicitModeller()}