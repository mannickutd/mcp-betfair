import os
import uvicorn


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


if __name__ == '__main__':
    uvicorn.run(
        'mcp_betfair.server:app', reload=True, reload_dirs=[str(THIS_DIR)]
    )
