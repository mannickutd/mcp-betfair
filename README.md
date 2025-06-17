# mcp-betfair
Example MCP server connected to betfair API
The idea is to show how to use the MCP protocol to connect to a third-party API, in this case, the Betfair API.
It has been built on top of the non live environment of Betfair API which may mean certain differences apply.

Information about the journey to place an order can be found (here)[https://betfair-datascientists.github.io/api/apiPythontutorial/#get-market-books] 
Information about the Betfair API can be found (here)[https://support.developer.betfair.com/hc/en-us] 
Betfair API visualization can be found (here)[https://apps.betfair.com/visualisers/api-ng-sports-operations/]



# Installation

```bash
uv sync
```

# Start the application

```bash
uv run python app.py
```

Open your browser and go to `http://localhost:8000/` to start the chat interface.


