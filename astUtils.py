
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
    def __init__(self, baseNode, nodeNameObj):
        self.colOffset = baseNode.col_offset
        self.lineNo = baseNode.lineno
        self.name = nodeNameObj.name
        self.asName = nodeNameObj.asname

    def __str__(self):
        importString = "Name: {0} is imported as {1}\n".format(self.name, self.asName)
        importString += "Col Offset is {0}\n".format(self.colOffset)
        importString += "Lineno is {0}\n\n".format(self.lineNo)
        return importString

class AstFromImport(AstImport):
    def __init__(self, baseNode, nodeNameObj):
        super(AstFromImport, self).__init__(baseNode, nodeNameObj)
        self.module = baseNode.module

class AstFunctionDef(object):
    def __init__(self, node):
        self.node = node
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

class AstAttribute(object):
    def __init__(self, node):
        self.colOffset = node.col_offset
        self.lineNo = node.lineno
        self.attr = node.attr
        self.ctx = node.ctx
        self.value = node.value

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
    def __init__(self, colOffset, lineNo, nodeName, dependencies):
        super(AstImportFix, self).__init__(colOffset, lineNo, nodeName)
        self.fixName = "{0} as _{0}".format(nodeName)
        self.dependencies = dependencies

    def __str__(self):
        importString = ""
        importString += "Col Offset is {0}\n".format(self.colOffset)
        importString += "Lineno is {0}\n".format(self.lineNo)
        importString += "NodeName is {0}\n".format(self.nodeName)
        importString += "FixName is {0}\n\n".format(self.fixName)
        return importString

class AstNotUsedFix(AstFix):
    def __init__(self, colOffset, lineNo, nodeName):
        super(AstNotUsedFix, self).__init__(colOffset, lineNo, nodeName)
        self.fixName = ""

    def __str__(self):
        importString = ""
        importString += "Col Offset is {0}\n".format(self.colOffset)
        importString += "Lineno is {0}\n".format(self.lineNo)
        importString += "NodeName is {0}\n".format(self.nodeName)
        importString += "FixName is {0}\n\n".format(self.fixName)
        return importString
