from typing import List
from tableauscraper.TableauWorksheet import TableauWorksheet
import tableauscraper
import copy


class TableauWorkbook:

    worksheets: List[TableauWorksheet] = []
    cmdResponse: bool = False
    _originalData = {}
    _originalInfo = {}
    _scraper = None

    def __init__(self, scraper, originalData, originalInfo, data, cmdResponse=False):
        self._scraper = scraper
        self.worksheets = data
        self.cmdResponse = cmdResponse
        self._originalData = originalData
        self._originalInfo = originalInfo

    def updateFullData(self, cmdResponse):
        presModel = cmdResponse["vqlCmdResponse"]["layoutStatus"]["applicationPresModel"]
        dataSegments = presModel["dataDictionary"]["dataSegments"]
        dataSegmentscp = copy.deepcopy(dataSegments)
        keys = list(dataSegmentscp.keys())
        for key in keys:
            if dataSegmentscp[key] is not None:
                self._scraper.dataSegments[key] = dataSegmentscp[key]

    def getWorksheetNames(self):
        return tableauscraper.utils.getWorksheetNames(self)

    def getWorksheets(self):
        if self.cmdResponse:
            return tableauscraper.dashboard.getWorksheetsCmdResponse(
                self._scraper, self._originalData
            )
        else:
            return tableauscraper.dashboard.getWorksheets(
                self._scraper, self._originalData, self._originalInfo
            )

    def getWorksheet(self, worksheetName):
        if self.cmdResponse:
            return tableauscraper.dashboard.getWorksheetCmdResponse(
                self._scraper, self._originalData, worksheetName
            )
        else:
            return tableauscraper.dashboard.getWorksheet(
                self._scraper, self._originalData, self._originalInfo, worksheetName
            )

    def getParameters(self):
        if self.cmdResponse:
            presModel = self._originalData["vqlCmdResponse"]["layoutStatus"]["applicationPresModel"]
            return tableauscraper.utils.getParameterControlVqlResponse(presModel)
        else:
            return tableauscraper.utils.getParameterControlInput(self._originalInfo)

    def setParameter(self, inputName, value):
        parameterNames = []
        if self.cmdResponse:
            presModel = self._originalData["vqlCmdResponse"]["layoutStatus"]["applicationPresModel"]
            parameterNames = [
                t["parameterName"]
                for t in tableauscraper.utils.getParameterControlVqlResponse(presModel)
                if t["column"] == inputName
            ]
        else:
            parameterNames = [
                t["parameterName"]
                for t in tableauscraper.utils.getParameterControlInput(self._originalInfo)
                if t["column"] == inputName
            ]
        if len(parameterNames) == 0:
            self._scraper.logger.error(f"column {inputName} not found")
            return TableauWorkbook(
                scraper=self._scraper,
                originalData=self._originalData,
                originalInfo=self._originalInfo,
                data=list(),
                cmdResponse=self.cmdResponse,
            )

        r = tableauscraper.api.setParameterValue(
            self._scraper, parameterNames[0], value
        )
        self.updateFullData(r)
        return tableauscraper.dashboard.getWorksheetsCmdResponse(self._scraper, r)

    def getSheets(self):
        presModel = tableauscraper.utils.getPresModelVizInfo(
            self._originalInfo)
        return [
            {
                "sheet": t["sheet"],
                "isDashboard": t["isDashboard"],
                "isVisible": t["isVisible"],
                "namesOfSubsheets": t["namesOfSubsheets"],
                "windowId": t["windowId"]
            }
            for t in presModel["workbookPresModel"]["sheetsInfo"]
        ]

    def goToSheet(self, sheetName):
        windowId = [
            t["windowId"]
            for t in self.getSheets()
            if t["sheet"] == sheetName
        ]
        if len(windowId) == 0:
            self._scraper.logger.error(f"sheet {sheetName} not found")
            return TableauWorkbook(
                scraper=self._scraper,
                originalData=self._originalData,
                originalInfo=self._originalInfo,
                data=list(),
                cmdResponse=self.cmdResponse,
            )
        r = tableauscraper.api.goToSheet(self._scraper, windowId[0])
        self.updateFullData(r)
        self._scraper.dashboard = sheetName
        return tableauscraper.dashboard.getWorksheetsCmdResponse(self._scraper, r)
