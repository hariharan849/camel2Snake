import sys
sys.path.append(r'c:\users\hariharan\appdata\local\programs\python\python37-32\lib\site-packages')
from collections import OrderedDict
from functools import reduce
import ast as _ast
import re as _re
import astUtils as _astUtils

IMPORT = "import"
FROM_IMPORT = "from import"
FUNCTION_DEF = "function"
NAME = "name"
ATTR = "attributes"
CALL = "call"
NOT_USED = "NOT_USED"

def _convertCamelToSnake(inputString):
    plainString = inputString.replace("_", "")
    if plainString[0].isupper():
        return inputString
    inputString = _re.sub('(.)([A-Z][a-z]+)', r'\1_\2', inputString)
    inputString = _re.sub('(.)([0-9]+)', r'\1_\2', inputString)
    return _re.sub('([a-z0-9])([A-Z])', r'\1_\2', inputString).lower()

class Analyzer(_ast.NodeVisitor):
    def __init__(self):
        self._usedNames = self._usedAttrs = set()
        self._codeInfo = OrderedDict()
        self._codeFix = OrderedDict()
        self._codeFix[NOT_USED] = OrderedDict()
        for nodeType in (IMPORT, FROM_IMPORT, NAME):
            self._codeFix[NOT_USED][nodeType] = OrderedDict()
        self._codeFix[IMPORT] = OrderedDict()
        self._codeFix[FROM_IMPORT] = OrderedDict()
        self._codeFix[NAME] = OrderedDict()
        self._codeFix["function"] = OrderedDict()
        self._codeFix["attr"] = OrderedDict()
        self._importDependencies = []

    def _importFix(self, nodeValues, nodeType):
        for (importName, importValue) in nodeValues.items():
            if importValue.asName is None and importValue.name not in self._usedNames:
                importFix = _astUtils.AstNotUsedFix(
                    importValue.colOffset,
                    importValue.lineNo,
                    importValue.name
                )
                if importValue.name in self._codeFix[NOT_USED][nodeType]:
                    self._codeFix[NOT_USED][nodeType][importValue.name].append(importFix)
                else:
                    self._codeFix[NOT_USED][nodeType][importValue.name] = [importFix]
                continue
            elif importValue.asName is not None and importValue.asName not in self._usedNames:
                if importValue.asName is None and importValue.name not in self._usedNames:
                    importFix = _astUtils.AstNotUsedFix(
                        importValue.colOffset,
                        importValue.lineNo,
                        importValue.asName
                    )
                    if importValue.asName in self._codeFix[NOT_USED][nodeType]:
                        self._codeFix[NOT_USED][nodeType][importValue.asName].append(importFix)
                    else:
                        self._codeFix[NOT_USED][nodeType][importValue.asName] = [importFix]
                    continue

            if importValue.asName is not None:
                continue

            dependencies = self._codeInfo[NAME].get(importValue.name)
            if dependencies:
                self._importDependencies.append(importValue.name)
            importFix = _astUtils.AstImportFix(
                importValue.colOffset,
                importValue.lineNo,
                importValue.name,
                dependencies
            )
            self._codeFix[nodeType][importValue.name] = importFix

    def _functionFix(self, nodeValues):
        for (funcName, funcValue) in nodeValues.items():
            convertedCase = _convertCamelToSnake(funcName)
            funcFix = _astUtils.AstFunctionFix(
                funcValue.colOffset,
                funcValue.lineNo,
                funcValue.name,
                convertedCase
            )
            self._codeFix["function"][funcName] = funcFix
            for argObj in funcValue.args:
                convertedCase = _convertCamelToSnake(argObj.name)
                nameFix = _astUtils.AstNameFix(
                    argObj.colOffset,
                    argObj.lineNo,
                    argObj.name,
                    convertedCase
                )
                self._codeFix["name"][argObj.name] = nameFix


    def _nameFix(self, nodeValues):
        for (varName, varValue) in nodeValues.items():
            if varName in self._importDependencies:
                continue

            for nameValue in varValue:
                convertedCase = _convertCamelToSnake(nameValue.name)
                if convertedCase != nameValue.name:
                    nameFix = _astUtils.AstNameFix(
                        nameValue.colOffset,
                        nameValue.lineNo,
                        nameValue.name,
                        convertedCase
                    )
                    self._codeFix["name"][varName] = nameFix

    def _attrFix(self, nodeValues):
        for (varName, varValue) in nodeValues.items():
            if varName in self._importDependencies:
                continue

            for nameValue in varValue:
                convertedCase = _convertCamelToSnake(nameValue.attr)
                if convertedCase != nameValue.attr:
                    nameFix = _astUtils.AstNameFix(
                        nameValue.colOffset,
                        nameValue.lineNo,
                        nameValue.attr,
                        convertedCase
                    )
                    self._codeFix["attr"][varName] = nameFix


    def _addNodeKey(self, nodeDict, name, nodeObj):
        if name in nodeDict:
            nodeDict[name].update(nodeObj)
        else:
            nodeDict[name] = nodeObj

    def execFix(self):
        for nodeType, nodeValues in self._codeInfo.items():
            if nodeType in (IMPORT, FROM_IMPORT):
                self._importFix(nodeValues, nodeType)

            elif nodeType == FUNCTION_DEF:
                self._functionFix(nodeValues)

            elif nodeType == NAME:
                self._nameFix(nodeValues)

            elif nodeType == ATTR:
                self._attrFix(nodeValues)

        return self._codeFix

    def _genericImportVisit(self, node, importType):
        importNames = OrderedDict()
        for nodeNameObj in node.names:
            importName = nodeNameObj.asname if nodeNameObj.asname else nodeNameObj.name
            importNames[importName] = importType(node, nodeNameObj)
        return importNames

    def visit_Import(self, node):
        self._addNodeKey(
            self._codeInfo,
            IMPORT,
            self._genericImportVisit(node, _astUtils.AstImport)
        )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self._addNodeKey(
            self._codeInfo,
            FROM_IMPORT,
            self._genericImportVisit(node, _astUtils.AstFromImport)
        )
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if FUNCTION_DEF not in self._codeInfo:
            self._codeInfo[FUNCTION_DEF] = OrderedDict()

        nameObj = _astUtils.AstFunctionDef(node)
        self._codeInfo[FUNCTION_DEF][node.name] = nameObj

        self.generic_visit(node)

    def _genericVisitName(self, node):
        if NAME not in self._codeInfo:
            self._codeInfo[NAME] = OrderedDict()

        nameObj = _astUtils.AstName(node)
        nameValues = self._codeInfo[NAME].get(node.id)
        if nameValues:
            self._codeInfo[NAME][node.id].append(nameObj)
        else:
            self._codeInfo[NAME][node.id] = [nameObj]

    def _genericVisitAttribute(self, node):
        if ATTR not in self._codeInfo:
            self._codeInfo[ATTR] = OrderedDict()

        nameObj = _astUtils.AstAttribute(node)
        nameValues = self._codeInfo[ATTR].get(node.attr)
        if nameValues:
            self._codeInfo[ATTR][node.attr].append(nameObj)
        else:
            self._codeInfo[ATTR][node.attr] = [nameObj]

    def visit_Name(self, node):
        self._genericVisitName(node)
        self._usedNames.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if ATTR not in self._codeInfo:
            self._codeInfo[ATTR] = OrderedDict()

        if isinstance(node.ctx, _ast.Load):
            self._genericVisitAttribute(node)
            self._usedAttrs.add(node.attr)
        if isinstance(node.value, _ast.Name):
            self._genericVisitName(node.value)
            self._usedNames.add(node.value.id)

    def generic_visit(self, node):
        super().generic_visit(node)

def parseFile(filename):
    with open(filename, "r") as file:
        return _ast.parse(file.read(), filename=filename)
