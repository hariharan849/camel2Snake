import sys
sys.path.append(r'c:\users\hariharan\appdata\local\programs\python\python37-32\lib\site-packages')
from collections import OrderedDict
from functools import reduce
import ast as _ast
import codegen as _codegen
import astunparse

IMPORT = "import"
FROM_IMPORT = "from import"
FUNCTION_DEF = "function"
NAME = "name"

def _convertCamelToSnake(inputString):
    if inputString.isupper():
        return
    return reduce(lambda x, y: x + ('_' if y.isupper() else '') + y, inputString).lower()


class _ImportObj(object):
    def __init__(self, node):
        self.name = node.name
        self.asName = node.asname

    def __str__(self):
        return "Name: {0} is imported as {1}\n".format(self.name, self.asName)

class _ArgumentObj(object):
    def __init__(self, argumentObj):
        self.name = argumentObj.arg
        self.lineNo = argumentObj.lineno
        self.colOffset = argumentObj.col_offset

    def __str__(self):
        return "Argument Name: {0}\n".format(self.name)

class AstImport(object):
    def __init__(self, node):
        self.colOffset = node.col_offset
        self.lineNo = node.lineno
        self.namesInfo = []
        for nodeName in node.names:
            self.namesInfo.append(_ImportObj(nodeName))

    def __str__(self):
        importString = ""
        for nodeInfo in self.namesInfo:
            importString += str(nodeInfo)
        importString += "Col Offset is {0}\n".format(self.colOffset)
        importString += "Lineno is {0}\n\n".format(self.lineNo)
        return importString

class AstFromImport(AstImport):
    def __init__(self, node):
        super(AstFromImport, self).__init__(node)
        self.module = node.module

class AstFunctionDef(object):
    def __init__(self, node):
        self.args = []

        for argumentObj in node.args.args:
            self.args.append(_ArgumentObj(argumentObj))

        self.body = node.body
        self.colOffset = node.col_offset
        self.decorator_list = node.decorator_list
        self.lineNo = node.lineno
        self.name = node.name
        self.returns = node.returns

class AstName(object):
    def __init__(self, node):
        self.colOffset = node.col_offset
        self.lineNo = node.lineno
        self.name = node.id

class AstFix(object):
    def __init__(self, colOffset, lineNo, nodeName):
        self.colOffset = colOffset
        self.lineNo = lineNo
        self.nodeName = nodeName

class AstFunctionFix(AstFix):
    def __init__(self, colOffset, lineNo, nodeName, fixName):
        super(AstFunctionFix, self).__init__(colOffset, lineNo, nodeName)
        self.fixName = fixName

class AstNameFix(AstFunctionFix):
    pass

class AstImportFix(AstFix):
    def __init__(self, colOffset, lineNo, nodeName):
        super(AstImportFix, self).__init__(colOffset, lineNo, nodeName)
        self.fixName = "{0} as _{0}".format(nodeName)

    def __str__(self):
        importString = ""
        importString += "Col Offset is {0}\n".format(self.colOffset)
        importString += "Lineno is {0}\n".format(self.lineNo)
        importString += "NodeName is {0}\n".format(self.nodeName)
        importString += "FixName is {0}\n\n".format(self.fixName)
        return importString

# class AstFromImport(object):
#     def __init__(self, node):
#         self._node = node
#         self._name = node.module
#         self._lineno = node.lineno
#         self._colOffset = node.col_offset
#         self._level = node.level
#         self._child = []
#
#         for alias in node.names:
#             self._child.append(type(alias.name, (object,), {'name': alias.name, 'asname': alias.asname}))
#
#     def __str__(self):
#         buildString = "{0}:\n".format(self._name)
#
#         for child in self._child:
#             buildString += child.name
#             if child.asname:
#                 buildString += " imported as {1}.".format(child.name, child.asname)
#                 buildString += "\n"
#
#         return buildString
#


# for node in ast.walk(root):
#         if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
#             yield node.id
#         elif isinstance(node, ast.Attribute):
#             yield node.attr
#         elif isinstance(node, ast.FunctionDef):
#             yield node.name

class Analyzer(_ast.NodeVisitor):
    def __init__(self):
        self._codeInfo = OrderedDict()
        self._codeFix = OrderedDict()

    def _importFix(self, nodeValues):
        for importValue in nodeValues:
            for nodeName in importValue.namesInfo:
                if nodeName.asName is not None:
                    continue
                self._addNodeKey(
                    self._codeFix,
                    IMPORT,
                    AstImportFix(
                        importValue.colOffset,
                        importValue.lineNo,
                        nodeName.name
                    )
                )

    def _functionFix(self, nodeValues):
        for funcValue in nodeValues:
            convertedCase =  _convertCamelToSnake(funcValue.name)
            if convertedCase != funcValue.name:
                self._addNodeKey(
                    self._codeFix,
                    FUNCTION_DEF,
                    AstFunctionFix(
                        funcValue.colOffset,
                        funcValue.lineNo,
                        funcValue.name,
                        convertedCase
                    )
                )

            for argument in funcValue.args:
                convertedCase = _convertCamelToSnake(argument.name)
                if convertedCase != argument.name:
                    self._addNodeKey(
                        self._codeFix,
                        FUNCTION_DEF,
                        AstFunctionFix(
                            argument.colOffset,
                            argument.lineNo,
                            argument.name,
                            convertedCase
                        )
                    )

    def _nameFix(self, nodeValues):
        for nameValue in nodeValues:
            convertedCase =  _convertCamelToSnake(nameValue.name)
            if convertedCase != nameValue.name:
                self._addNodeKey(
                    self._codeFix,
                    NAME,
                    AstFunctionFix(
                        nameValue.colOffset,
                        nameValue.lineNo,
                        nameValue.name,
                        convertedCase
                    )
                )

    def _addNodeKey(self, nodeDict, name, nodeObj):
        if name in nodeDict:
            nodeDict[name].append(nodeObj)
        else:
            nodeDict[name] = [nodeObj]

    def visit_Import(self, node):
        self._addNodeKey(self._codeInfo, IMPORT, AstImport(node))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self._addNodeKey(self._codeInfo, IMPORT, AstFromImport(node))
        self.generic_visit(node)

    def execFix(self):
        for nodeType, nodeValues in self._codeInfo.items():
            if nodeType in (IMPORT, FROM_IMPORT):
                self._importFix(nodeValues)

            elif nodeType == FUNCTION_DEF:
                self._functionFix(nodeValues)

            elif nodeType == NAME:
                self._nameFix(nodeValues)

        # for nodeType, nodeValues in self._codeFix.items():
        #     for val in nodeValues:
        #         print (val)

        print (self._codeFix)
        return self._codeFix

    def visit_FunctionDef(self, node):
        self._addNodeKey(self._codeInfo, FUNCTION_DEF, AstFunctionDef(node))
        self.generic_visit(node)

    def visit_Name(self, node):
        self._addNodeKey(self._codeInfo, NAME, AstName(node))
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, _ast.Call):
            print (dir(node.value))
            print (node.value.func.id, 'call')

    def generic_visit(self, node):
        super().generic_visit(node)
        print (type(node))
#
#     # def visit_ClassDef(self, node):
#     #     print (node.name, "Class")
#     #     self.generic_visit(node)
#
#     def report(self):
#         print(self.stats)

# class

# class StaticmethodChecker(object):
#     def __init__(self, tree):
#         self.tree = tree
#         self.stats = defaultdict(list)
#
#     def _importFix(self, node):
#         keyName = "import" if isinstance(node, _ast.Import) else "importFrom"
#         for alias in node.names:
#             self.stats[keyName].append(alias.name)
#             if alias.asname:
#                 continue
#             alias.asname = "_{0}".format(alias.name)
#
#     def _assignNameFix(self, node):
#         for target in node.targets:
#             if isinstance(target, _ast.Name):
#                 print (_convertCamelToSnake(target.id), '==', target.id)
#
#     def run(self):
#         for stmt in _ast.walk(self.tree):
#             if isinstance(stmt, (_ast.Import, _ast.ImportFrom)):
#                 self._importFix(stmt)
#
#             elif isinstance(stmt, _ast.Assign):
#                 self._assignNameFix(stmt)
#
#             elif isinstance(stmt, _ast.ClassDef):
#                 for body_item in stmt.body:
#                     if isinstance(body_item, _ast.Assign):
#                         self._assignNameFix(body_item)
#                     # Not a method, skip
#                     if not isinstance(body_item, _ast.FunctionDef):
#                         continue
#                     # Check that it has a decorator
#                     print (_convertCamelToSnake(body_item.name))
#                     if _convertCamelToSnake(body_item.name) == "run":
#                         for fun_item in body_item.body:
#                             print (fun_item, '=run=========')
#                     for decorator in body_item.decorator_list:
#                         if (isinstance(decorator, _ast.Name)
#                                 and decorator.id == 'staticmethod'):
#                             # It's a static function, it's OK
#                             break
#                     else:
#                         try:
#                             first_arg = body_item.args.args[0]
#                             for argument in body_item.args.args[1:]:
#                                 print (_convertCamelToSnake(argument.arg), "argu,ment")
#                         except IndexError:
#                             print (
#                                 body_item.lineno,
#                                 body_item.col_offset,
#                                 "H905: method misses first argument",
#                                 "H905",
#                             )
#                             # Check next method
#                             continue
#                         for func_stmt in _ast.walk(body_item):
#                             if isinstance(func_stmt, _ast.Name):
#                                 print (_convertCamelToSnake(argument.arg), "method name")
#                             if (func_stmt != first_arg
#                                     and isinstance(func_stmt, _ast.Name)
#                                     and func_stmt.id == first_arg.arg):
#                                 # The first argument is used, it's OK
#                                 break
#                         else:
#                             print (
#                                 body_item.lineno,
#                                 body_item.col_offset,
#                                 "H904: method should be declared static",
#                                 "H904",
#                             )
#             # Ignore non-class
#             # print type(stmt)#, _ast.ImportFrom)
#                 # continue
#
#     def report(self):
#         print(self.stats)

def parseFile(filename):
    with open(filename, "r") as file:
        return _ast.parse(file.read(), filename=filename)

if __name__ == "__main__":
    filename = r'E:\python\textDifference\test.py'

    tree = parseFile(filename)
    # analyzer = StaticmethodChecker(tree)
    # analyzer.run()
    # analyzer.report()

    #
    # print (_codegen.to_source(tree))
    # print (textLines)
    analyzer = Analyzer()
    analyzer.visit(tree)
    analyzer.execFix()

    print ("===============")
    # print (astunparse.unparse(tree))
    # print (_codegen.to_source(tree))
    # analyzer.report()
    # for f in tree.body:
    #     if isinstance(f, _ast.ClassDef):
    #         for t in f.body:
    #             print (type(t))
    # for func in top_level_functions(tree.body):
    #     print("  %s" % func.name)