import pandas as pd
import tableauscraper
from typing import List
from tableauscraper import utils
import copy


class TableauWorksheet:

    name: str = ""
    data: pd.DataFrame = pd.DataFrame()
    cmdResponse: bool = False

    _originalData = {}
    _originalInfo = {}
    _data_dictionnary = {}
    _scraper = None

    def __init__(
        self,
        scraper,
        originalData,
        originalInfo,
        worksheetName,
        dataFrame,
        dataFull,
        cmdResponse=False,
    ):
        self._scraper = scraper
        self.name = worksheetName
        self.data = dataFrame
        self._originalData = originalData
        self._originalInfo = originalInfo
        self.cmdResponse = cmdResponse
        self._data_dictionnary = dataFull
        # if self.cmdResponse:
        #     presModel = self._originalData["vqlCmdResponse"]["layoutStatus"][
        #         "applicationPresModel"
        #     ]
        #     self._data_dictionnary = tableauscraper.utils.getDataFullCmdResponse(
        #         presModel, self._scraper.dataSegments
        #     )
        # else:
        #     presModel = tableauscraper.utils.getPresModelVizData(
        #         self._originalData)
        #     self._data_dictionnary = tableauscraper.utils.getDataFull(
        #         presModel, self._scraper.dataSegments)

    def updateFullData(self, cmdResponse):
        presModel = cmdResponse["vqlCmdResponse"]["layoutStatus"]["applicationPresModel"]
        dataSegments = presModel["dataDictionary"]["dataSegments"]
        dataSegmentscp = copy.deepcopy(dataSegments)
        keys = list(dataSegmentscp.keys())
        for key in keys:
            if dataSegmentscp[key] is not None:
                self._scraper.dataSegments[key] = dataSegmentscp[key]

    def getColumns(self) -> List[str]:
        if self.cmdResponse:
            presModel = self._originalData["vqlCmdResponse"]["layoutStatus"]["applicationPresModel"]
            return [
                t["fieldCaption"]
                for t in tableauscraper.utils.getIndicesInfoVqlResponse(
                    presModel, self.name, noSelectFilter=True
                )
            ]
        else:
            presModel = tableauscraper.utils.getPresModelVizData(
                self._originalData)
            return [
                t["fieldCaption"]
                for t in tableauscraper.utils.getIndicesInfo(
                    presModel, self.name, noSelectFilter=True
                )
            ]

    def getSelectableColumns(self) -> List[str]:
        if self.cmdResponse:
            presModel = self._originalData["vqlCmdResponse"]["layoutStatus"]["applicationPresModel"]
            return [
                t["fieldCaption"]
                for t in tableauscraper.utils.getIndicesInfoVqlResponse(
                    presModel, self.name, noSelectFilter=False
                )
            ]
        else:
            presModel = tableauscraper.utils.getPresModelVizData(
                self._originalData)
            return [
                t["fieldCaption"]
                for t in tableauscraper.utils.getIndicesInfo(
                    presModel, self.name, noSelectFilter=False
                )
            ]

    def getValues(self, column) -> List[str]:
        if self.cmdResponse:
            presModel = self._originalData["vqlCmdResponse"]["layoutStatus"]["applicationPresModel"]
            columnObj = [
                t
                for t in tableauscraper.utils.getIndicesInfoVqlResponse(
                    presModel, self.name, noSelectFilter=True
                )
                if t["fieldCaption"] == column
            ]
            if len(columnObj) == 0:
                return []
            frameData = tableauscraper.utils.getDataCmdResponse(
                self._data_dictionnary, [columnObj[0]]
            )
            frameDataKeys = list(frameData.keys())

            if len(frameDataKeys) == 0:
                return []
            return frameData[frameDataKeys[0]]
        else:
            presModel = tableauscraper.utils.getPresModelVizData(
                self._originalData)
            columnObj = [
                t
                for t in tableauscraper.utils.getIndicesInfo(
                    presModel, self.name, noSelectFilter=True
                )
                if t["fieldCaption"] == column
            ]
            if len(columnObj) == 0:
                return []
            frameData = tableauscraper.utils.getData(
                self._data_dictionnary, [columnObj[0]]
            )
            frameDataKeys = list(frameData.keys())

            if len(frameDataKeys) == 0:
                return []
            return frameData[frameDataKeys[0]]

    def getTupleIds(self, column) -> List[int]:
        if self.cmdResponse:
            presModel = self._originalData["vqlCmdResponse"]["layoutStatus"]["applicationPresModel"]
            columnObj = [
                t
                for t in tableauscraper.utils.getIndicesInfoVqlResponse(
                    presModel, self.name, noSelectFilter=True, noFieldCaption=True
                )
                if t["fn"] == "[system:visual].[tuple_id]"
            ]
            if len(columnObj) == 0:
                return []

            return columnObj[0]["tupleIds"]
        else:
            presModel = tableauscraper.utils.getPresModelVizData(
                self._originalData)
            columnObj = [
                t
                for t in tableauscraper.utils.getIndicesInfo(
                    presModel, self.name, noSelectFilter=True, noFieldCaption=True
                )
                if t["fn"] == "[system:visual].[tuple_id]"
            ]
            if len(columnObj) == 0:
                return []
            return columnObj[0]["tupleIds"]

    def select(self, column, value):
        values = self.getValues(column)
        tupleIds = self.getTupleIds(column)
        try:
            index = values.index(value)
            if len(tupleIds) > index:
                index = tupleIds[index]
            else:
                index = index + 1
            r = tableauscraper.api.select(self._scraper, self.name, [index])
            self.updateFullData(r)
            return tableauscraper.dashboard.getWorksheetsCmdResponse(self._scraper, r)
        except ValueError:
            return tableauscraper.TableauDashboard(
                scraper=self._scraper, originalData={}, originalInfo={}, data=[]
            )
