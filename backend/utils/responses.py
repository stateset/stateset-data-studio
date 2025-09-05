from fastapi.responses import ORJSONResponse

def json_response(data: dict | list, **headers):
    resp = ORJSONResponse(content=data)
    for k, v in headers.items():
        resp.headers[k] = v
    return resp
