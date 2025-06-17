import datetime as dt
from typing import Annotated, List, Optional
import requests
from pydantic import BaseModel, Field


class BetfairEventType(BaseModel):
    id: Annotated[int, Field(alias='id')]
    name: Annotated[str, Field(alias='name')]


class BetfairCompetition(BaseModel):
    id: Annotated[int, Field(alias='id')]
    name: Annotated[str, Field(alias='name')]
    region: Annotated[str, Field(alias='region', default=None)]


class BetfairEvent(BaseModel):
    id: Annotated[int, Field(alias='id')]
    event: Annotated[str, Field(alias='name')]
    country_code: Annotated[str, Field(alias='countryCode', default=None)]
    timezone: Annotated[str, Field(alias='timezone')]
    open_date: Annotated[dt.datetime, Field(alias='openDate')]


class BetfairMarketCatalogue(BaseModel):
    market_id: Annotated[str, Field(alias='marketId')]
    market_name: Annotated[str, Field(alias='marketName')]
    total_matched: Annotated[float, Field(alias='totalMatched', default=0.0)]


class BetfairMarketType(BaseModel):
    market_type: Annotated[str, Field(alias='marketType')]
    market_count: Annotated[int, Field(alias='marketCount')]


class BetfairMarketBookSelection(BaseModel):
    market_id: Annotated[str, Field(alias='marketId')]
    is_market_data_delayed: Annotated[bool, Field(alias='isMarketDataDelayed')]
    status: Annotated[str, Field(alias='status')]
    bet_delay: Annotated[int, Field(alias='betDelay')]
    bsp_reconciled: Annotated[bool, Field(alias='bspReconciled')]
    complete: Annotated[bool, Field(alias='complete')]
    inplay: Annotated[bool, Field(alias='inplay')]
    number_of_winners: Annotated[int, Field(alias='numberOfWinners')]
    number_of_runners: Annotated[int, Field(alias='numberOfRunners')]
    number_of_active_runners: Annotated[int, Field(alias='numberOfActiveRunners')]
    total_matched: Annotated[float, Field(alias='totalMatched')]
    total_available: Annotated[float, Field(alias='totalAvailable')]
    cross_matching: Annotated[bool, Field(alias='crossMatching')]
    runners_voidable: Annotated[bool, Field(alias='runnersVoidable')]
    version: Annotated[int, Field(alias='version')]
    selection_id: Annotated[int, Field(alias='selectionId')]
    handicap: Annotated[float, Field(alias='handicap', default=0.0)]
    status: Annotated[str, Field(alias='status')]
    total_matched: Annotated[float, Field(alias='totalMatched', default=0.0)]


class BetfairClient:
    def __init__(self, api_key: str, session_token: str):
        self.api_key = api_key
        self.session_token = session_token
        self.base_url = "https://apps.betfair.com/visualisers/betting"

    def _headers(self):
        return {
            "X-Application": self.api_key,
            "X-Authentication": self.session_token,
            "Content-Type": "application/json",
        }

    def make_request(self, method: str = 'POST', data=None):
        url = f"{self.base_url}"
        response = requests.request(method, url, headers=self._headers(), json=data)
        response.raise_for_status()
        return response.json()

    def list_event_types(self) -> List[BetfairEventType]:
        """
        List all event types available on Betfair.
        :return:
        """
        endpoint = "listEventTypes"
        data = [{
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listEventTypes",
            "params": {"filter": {}},
            "id": 1,
        }]
        retval = self.make_request(data=data)
        if len(retval) == 1:
            retval = retval[0]  # Unwrap the single item response
        if "result" in retval:
            retval = [BetfairEventType(**item['eventType']) for item in retval["result"]]
        else:
            retval = []
        return retval

    def list_competitions(self,
        text_query: Optional[str] = None,
        exchange_ids: Optional[List[int]] = None,
        event_ids: Optional[List[int]] = None,
        event_type_ids: Optional[List[int]] = None,
    ) -> List[BetfairCompetition]:
        """
        List competitions based on various filters.

        :param text_query: Text query to filter competitions.
        :param exchange_ids: List of exchange IDs to filter competitions.
        :param event_ids: List of event IDs to filter competitions.
        :param event_type_ids: List of event type IDs to filter competitions.
        :return: List of competitions matching the criteria.
        """
        endpoint = "listCompetitions"
        filter = {}
        if text_query:
            filter["textQuery"] = text_query
        if exchange_ids:
            filter["exchangeIds"] = exchange_ids
        if event_ids:
            filter["eventIds"] = event_ids
        if event_type_ids:
            filter["eventTypeIds"] = event_type_ids
        data = [{
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listCompetitions",
            "params": {
                "filter": filter
            },
            "id": 1,
        }]
        retval = self.make_request(data=data)
        if len(retval) == 1:
            retval = retval[0]  # Unwrap the single item response
        if "result" in retval:
            retval = [BetfairCompetition(**item['competition']) for item in retval["result"]]
        else:
            retval = []
        return retval

    def list_events(
        self,
        text_query: Optional[str] = None,
        exchange_ids: Optional[List[int]] = None,
        event_ids: Optional[List[int]] = None,
        event_type_ids: Optional[List[int]] = None,
        competition_ids: Optional[List[int]] = None,
        market_ids: Optional[List[int]] = None,
        venues: Optional[List[str]] = None,
        market_start_time: Optional[dt.datetime] = None,
        market_end_time: Optional[dt.datetime] = None,
    ) -> List[BetfairEvent]:
        """
        List events based on various filters.

        :param text_query: Text query to filter events.
        :param exchange_ids: List of exchange IDs to filter events.
        :param event_ids: List of event IDs to filter events.
        :param event_type_ids: List of event type IDs to filter events.
        :param competition_ids: List of competition IDs to filter events.
        :param market_ids: List of market IDs to filter events.
        :param venues: List of venues to filter events.
        :param market_start_time: Start time for the market.
        :param market_end_time: End time for the market.
        :return: List of events matching the criteria.
        """
        endpoint = "listEvents"
        filter = {}
        if text_query:
            filter["textQuery"] = text_query
        if exchange_ids:
            filter["exchangeIds"] = exchange_ids
        if event_ids:
            filter["eventIds"] = event_ids
        if event_type_ids:
            filter["eventTypeIds"] = event_type_ids
        if competition_ids:
            filter["competitionIds"] = competition_ids
        if market_ids:
            filter["marketIds"] = market_ids
        if venues:
            filter["venues"] = venues
        if market_start_time or market_end_time:
            filter["marketStartTime"] = {}
            if market_start_time:
                filter["marketStartTime"]["from"] = market_start_time.isoformat()
            if market_end_time:
                filter["marketStartTime"]["to"] = market_end_time.isoformat()
        data = [{
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listEvents",
            "params": {
                "filter": filter
            },
            "id": 1,
        }]
        retval = self.make_request(data=data)
        if len(retval) == 1:
            retval = retval[0]  # Unwrap the single item response
        if "result" in retval:
            retval = [BetfairEvent(**item['event']) for item in retval["result"]]
        else:
            retval = []
        return retval

    def list_market_types(
        self,
        exchange_ids: Optional[List[int]] = None,
        event_ids: Optional[List[int]] = None,
        event_type_ids: Optional[List[int]] = None,
        competition_ids: Optional[List[int]] = None,
        market_ids: Optional[List[int]] = None,
        start_time: Optional[dt.datetime] = None,
        end_time: Optional[dt.datetime] = None,
    ) -> BetfairMarketType:
        """
        List market types.

        :param exchange_ids: List of exchange IDs to filter market types.
        :param event_ids: List of event IDs to filter market types.
        :param event_type_ids: List of event type IDs to filter market types.
        :param competition_ids: List of competition IDs to filter market types.
        :param market_ids: List of market IDs to filter market types.
        :param start_time: Start time for the market.
        :param end_time: End time for the market.
        :return:
        """
        endpoint = "listMarketTypes"
        filter = {}
        if exchange_ids:
            filter["exchangeIds"] = exchange_ids
        if event_ids:
            filter["eventIds"] = event_ids
        if event_type_ids:
            filter["eventTypeIds"] = event_type_ids
        if competition_ids:
            filter["competitionIds"] = competition_ids
        if market_ids:
            filter["marketIds"] = market_ids
        if start_time or end_time:
            filter["marketStartTime"] = {}
            if start_time:
                filter["marketStartTime"]["from"] = start_time.isoformat()
            if end_time:
                filter["marketStartTime"]["to"] = end_time.isoformat()
        data = [{
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listMarketTypes",
            "params": {
                "filter": filter,
                "maxResults": 100,
                "marketProjection": ["MARKET_START_TIME", "RUNNER_DESCRIPTION"]
            },
            "id": 1,
        }]
        retval = self.make_request(data=data)
        if len(retval) == 1:
            retval = retval[0]  # Unwrap the single item response
        if "result" in retval:
            retval = [BetfairEvent(**item['event']) for item in retval["result"]]
        else:
            retval = []
        return retval

    def list_market_catalogue(
        self,
        event_ids: Optional[List[int]] = None,
        event_type_ids: Optional[List[int]] = None,
        market_ids: Optional[List[int]] = None,
        competition_ids: Optional[List[int]] = None,
        market_start_time: Optional[dt.datetime] = None,
        market_end_time: Optional[dt.datetime] = None,
    ) -> List[BetfairMarketCatalogue]:
        """
        List market catalogue.
        :param event_ids: List of event IDs to filter market catalogues.
        :param market_ids: List of market IDs to filter market catalogues.
        :param market_start_time: Start time for the market.
        :param market_end_time: End time for the market.

        :return: List of market catalogues.
        """
        endpoint = "listMarketCatalogue"
        filter = {}
        if event_ids:
            filter["eventIds"] = event_ids
        if event_type_ids:
            filter["eventTypeIds"] = event_type_ids
        if market_ids:
            filter["marketIds"] = market_ids
        if competition_ids:
            filter["competitionIds"] = competition_ids
        if market_start_time or market_end_time:
            filter["marketStartTime"] = {}
            if market_start_time:
                filter["marketStartTime"]["from"] = market_start_time.isoformat()
            if market_end_time:
                filter["marketStartTime"]["to"] = market_end_time.isoformat()
        data = [{
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listMarketCatalogue",
            "params": {
                "filter": filter,
                "maxResults": 100,
                "marketProjection": ["MARKET_START_TIME", "RUNNER_DESCRIPTION"]
            },
            "id": 1,
        }]
        retval = self.make_request(data=data)
        if len(retval) == 1:
            retval = retval[0]  # Unwrap the single item response
        if "result" in retval:
            retval = [BetfairMarketCatalogue(**item) for item in retval["result"]]
        else:
            retval = []
        return retval

    def list_market_book_selection(
        self,
        market_id: int,
    ) -> List[BetfairMarketBookSelection]:
        """
        List market book selection.
        ** If we then want to get the prices available/last traded for a market, we should use the listMarketBook operation.
        :param market_id: Market ID to filter market book selections.
        :return: List of market book selections.
        """
        endpoint = "listMarketBook"
        data = [{
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listMarketBook",
            "params": {
                "marketIds": [market_id],
                "priceProjection": {
                    "priceData": ["EX_BEST_OFFERS", "EX_TRADED"],
                    "virtualise": True,
                },
            },
            "id": 1,
        }]
        retval = self.make_request(data=data)
        if len(retval) == 1:
            retval = retval[0]
        if "result" in retval:
            for item in retval["result"]:
                base_item = dict([(k, v) for k, v in item.items() if k != "runners"])
                for runner in item.get("runners", []):
                    runner.update(base_item)
                    retval.append(
                        BetfairMarketBookSelection(**runner)
                    )
        else:
            retval = []
        return retval
