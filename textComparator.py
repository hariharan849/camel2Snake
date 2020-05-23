import sys
sys.path.append(r'c:\users\hariharan\appdata\local\programs\python\python37-32\lib\site-packages')
sys.path.append(r'E:\python\textDifference')

import os as _os
import ast as _ast
import tempfile as _tempfile
import difflib as _difflib
from PyQt5 import (
    QtGui as _QtGui,
    QtCore as _QtCore,
    Qsci as _Qsci,
    QtWidgets as _QtWidgets
)
import autopep8
from copy import copy
from PyQt5 import QtGui
from textEditor import SimplePythonEditor
import styleSheet
from pythonParser import Analyzer, parseFile


class TextComparator(_QtWidgets.QWidget):
    INDICATOR_UNIQUE_1 = 1
    INDICATOR_UNIQUE_2 = 2
    INDICATOR_SIMILAR = 3
    similarColor = _QtGui.QColor(0x8a, 0xe2, 0x34, 80)
    MARGIN_STYLE = _Qsci.QsciScintilla.STYLE_LINENUMBER

    def __init__(self, srcPath, parent=None):
        super(TextComparator, self).__init__(parent)
        
        self._initVariables(srcPath)
        self._createWidgets()
        self._layoutWidgets()
        self._connectWidgets()
        self._setStyleSheet()
        self._compareText()

        self.showMaximized()

    def _initVariables(self, srcPath):
        self._srcPath = srcPath
        fd, self._dstPath = _tempfile.mkstemp()

        with open(srcPath, 'r') as fileObj:
            srcLines = copy(fileObj.read())

        srcLines = autopep8.fix_code(srcLines, options={'aggressive': 1})
        codeFix = self._parseFile(srcLines)
        srcLines = srcLines.split("\n")

        for (nodeType, nodeValues) in codeFix.items():
            if nodeType == "NOT_USED":
                continue

            if nodeType in ("import", "from import"):
                for nodeName, nodeFix in nodeValues.items():
                    srcLine = srcLines[nodeFix.lineNo - 1]
                    if nodeFix.fixName:
                        srcLines[nodeFix.lineNo - 1] = srcLine.replace(nodeFix.nodeName, nodeFix.fixName)
                        for dependent in nodeFix.dependencies:
                            dependentLine = srcLines[dependent.lineNo - 1]
                            dependentLine = dependentLine[:dependent.colOffset] + "_"+nodeFix.nodeName.strip() + dependentLine[dependent.colOffset+len(nodeFix.nodeName):]
                            srcLines[dependent.lineNo-1] = dependentLine

            elif nodeType == "function":
                for nodeName, nodeFix in nodeValues.items():
                    srcLine = srcLines[nodeFix.lineNo - 1]
                    if nodeFix.fixName:
                        srcLines[nodeFix.lineNo - 1] = srcLine.replace(nodeFix.nodeName, nodeFix.fixName)

            elif nodeType in ["name", "attr"]:
                for nodeName, nodeFix in nodeValues.items():
                    srcLine = srcLines[nodeFix.lineNo - 1]
                    if nodeFix.fixName:
                        srcLines[nodeFix.lineNo - 1] = srcLine.replace(nodeFix.nodeName, nodeFix.fixName)

        if codeFix["NOT_USED"]:
            for actualNodeType, actualNodeValues in codeFix["NOT_USED"].items():

                for nodeName, nodeNameValues in actualNodeValues.items():
                    def fetchLineNo(val):
                        return val.lineNo

                    for unUsed in sorted(nodeNameValues, key=lambda val: fetchLineNo(val)):
                        del srcLines[unUsed.lineNo - 1]

        with _os.fdopen(fd, 'w') as df:
            for line in srcLines:
                df.write(line+'\n')
        
        self._unique1Color = _QtGui.QColor(0x72, 0x9f, 0xcf, 80)
        self._unique2Color = _QtGui.QColor(0xad, 0x7f, 0xa8, 80)
        self._focusedEditor = None

        imageScaleSize = _QtCore.QSize(16, 16)
        imageUnique1 = _QtGui.QPixmap(
            _os.path.join(_os.path.dirname(__file__), 'icons/diff-unique-1.png')
        )

        imageUnique2 = _QtGui.QPixmap(
            _os.path.join(_os.path.dirname(__file__), 'icons/diff-unique-2.png')
        )

        imageSimilar = _QtGui.QPixmap(
            _os.path.join(_os.path.dirname(__file__), 'icons/diff-similar.png')
        )
        # Scale the images to a smaller size
        self._imageUnique1 = imageUnique1.scaled(imageScaleSize)
        self._imageUnique2 = imageUnique2.scaled(imageScaleSize)
        self._imageSimilar = imageSimilar.scaled(imageScaleSize)

    def _createWidgets(self):
        self.editorPython1 = SimplePythonEditor(self._srcPath, self)
        self.editorPython2 = SimplePythonEditor(self._dstPath, self)
        self._focusedEditor = self.editorPython1
        self._focusedEditor.setFocus()

        for i, editor in enumerate((self.editorPython1, self.editorPython2), 1):
            # markers
            setattr(self, "_markerUnique{0}".format(i), editor.markerDefine(_Qsci.QsciScintillaBase.SC_MARK_BACKGROUND, 0))
            setattr(self, "_markerUniqueSymbol{0}".format(i), editor.markerDefine(self._imageUnique1, 1))
            setattr(self, "_markerSimilar{0}".format(i), editor.markerDefine(_Qsci.QsciScintillaBase.SC_MARK_BACKGROUND, 2))
            setattr(self, "_markerSimilarSymbol{0}".format(i), editor.markerDefine(self._imageSimilar, 3))
            #backgroundcolor
            editor.setMarkerBackgroundColor(
                getattr(self, "_unique{0}Color".format(i)),
                getattr(self, "_markerUnique{0}".format(i))
            )
            editor.setMarkerBackgroundColor(
                self.similarColor,
                getattr(self, "_markerSimilar{0}".format(i))
            )
            self._initMargin(editor)

    def _initMargin(self, editor):
        """Initialize margin for coloring lines showing diff symbols"""
        editor.setMarginWidth(0, "0")
        #Setting the margin width to 0 makes the marker colour the entire line
        #to the marker background color
        editor.setMarginWidth(1, "00")
        editor.setMarginWidth(2, 0)
        editor.setMarginType(0, _Qsci.QsciScintilla.TextMargin)
        editor.setMarginType(1, _Qsci.QsciScintilla.SymbolMargin)
        editor.setMarginType(2, _Qsci.QsciScintilla.SymbolMargin)

        editor.setMarginMarkerMask(
            1, ~_Qsci.QsciScintillaBase.SC_MASK_FOLDERS
        )
        editor.setMarginMarkerMask(
            2,
            0x0
        )

    def _layoutWidgets(self):
        layout = _QtWidgets.QGridLayout(self)
        layout.addWidget(self.editorPython1, 0, 0)
        layout.addWidget(self.editorPython2, 0, 1)

    def _addDecoratorToEditor(self):
        # Add decorators to each editors mouse clicks and mouse wheel scrolls
        def focusDecorator(functionTo, focusedEditor):
            def decoratedFunction(*args, **kwargs):
                self._focusedEditor = focusedEditor
                functionTo(*args, **kwargs)
            return decoratedFunction

        self.editorPython1.mousePressEvent = focusDecorator(
            self.editorPython1.mousePressEvent,
            self.editorPython1
        )
        self.editorPython1.wheelEvent = focusDecorator(
            self.editorPython1.wheelEvent,
            self.editorPython1
        )
        self.editorPython2.mousePressEvent = focusDecorator(
            self.editorPython2.mousePressEvent,
            self.editorPython2
        )
        self.editorPython2.wheelEvent = focusDecorator(
            self.editorPython2.wheelEvent,
            self.editorPython2
        )

    def _connectWidgets(self):
        self.editorPython1.SCN_UPDATEUI.connect(self._scnUpdateui)
        self.editorPython2.SCN_UPDATEUI.connect(self._scnUpdateui)
        self.editorPython1.cursorPositionChanged.connect(self._cursorChange)
        self.editorPython2.cursorPositionChanged.connect(self._cursorChange)
        self._addDecoratorToEditor()

    def _setStyleSheet(self):
        def setEditorTheme(editor):
            editor.resetFoldMarginColors()
            editor.setMarginsForegroundColor(styleSheet.LineMargin.ForeGround)
            editor.setMarginsBackgroundColor(styleSheet.LineMargin.BackGround)
            editor.SendScintilla(
                _Qsci.QsciScintillaBase.SCI_STYLESETBACK,
                _Qsci.QsciScintillaBase.STYLE_DEFAULT,
                styleSheet.Paper
            )
            editor.SendScintilla(
                _Qsci.QsciScintillaBase.SCI_STYLESETBACK,
                _Qsci.QsciScintillaBase.STYLE_LINENUMBER,
                styleSheet.LineMargin.BackGround
            )
            editor.SendScintilla(
                _Qsci.QsciScintillaBase.SCI_SETCARETFORE,
                styleSheet.Cursor
            )
        setEditorTheme(self.editorPython1)
        setEditorTheme(self.editorPython2)


    def _parseFile(self, srcLines):
        # tree = parseFile(self._srcPath)
        tree = _ast.parse(srcLines)
        analyzer = Analyzer()
        analyzer.visit(tree)
        return analyzer.execFix()

    def _compareText(self):
        """
        Compare two text strings and display the difference
        !! This function uses Python's difflib which is not 100% accurate !!
        """
        # Store the original text
        text1List = self.editorPython1.text().split("\n")
        text2List = self.editorPython2.text().split("\n")
        # Create the difference
        differer = _difflib.Differ()
        listSum = list(differer.compare(text1List, text2List))
        # Assemble the two lists of strings that will be displayed in each editor
        list_1 = []
        lineCounter_1 = 1
        lineNumbering_1 = []
        lineStyling_1 = []
        list_2 = []
        lineCounter_2 = 1
        lineNumbering_2 = []
        lineStyling_2 = []
        # Flow control flags
        skipNext = False
        storeNext = False
        for i, line in enumerate(listSum):
            if storeNext == True:
                storeNext = False
                list_2.append(line[2:])
                lineNumbering_2.append(str(lineCounter_2))
                lineCounter_2 += 1
                lineStyling_2.append(self.INDICATOR_SIMILAR)
            elif skipNext == False:
                if line.startswith("  "):
                    # The line is the same in both texts
                    list_1.append(line[2:])
                    lineNumbering_1.append(str(lineCounter_1))
                    lineCounter_1 += 1
                    lineStyling_1.append(None)
                    list_2.append(line[2:])
                    lineNumbering_2.append(str(lineCounter_2))
                    lineCounter_2 += 1
                    lineStyling_2.append(None)
                elif line.startswith("- "):
                    # The line is unique to text 1
                    list_1.append(line[2:])
                    lineNumbering_1.append(str(lineCounter_1))
                    lineCounter_1 += 1
                    lineStyling_1.append(self.INDICATOR_UNIQUE_1)
                    list_2.append("")
                    lineNumbering_2.append("")
                    lineStyling_2.append(None)
                elif line.startswith("+ "):
                    # The line is unique to text 2
                    list_1.append("")
                    lineNumbering_1.append("")
                    lineStyling_1.append(None)
                    list_2.append(line[2:])
                    lineNumbering_2.append(str(lineCounter_2))
                    lineCounter_2 += 1
                    lineStyling_2.append(self.INDICATOR_UNIQUE_2)
                elif line.startswith("? "):
                    # The line is similar
                    if (listSum[i - 1].startswith("- ") and
                            listSum[i + 1].startswith("+ ") and
                            listSum[i + 2].startswith("? ")):
                        """
                        Line order:
                            - ...
                            ? ...
                            + ...
                            ? ...
                        """
                        # Lines have only a few character difference, skip the
                        # first '?' and handle the next '?' as a "'- '/'+ '/'? '" sequence
                        pass
                    elif listSum[i - 1].startswith("- "):
                        # Line in text 1 has something added
                        """
                        Line order:
                            - ...
                            ? ...
                            + ...
                        """
                        lineStyling_1[len(lineNumbering_1) - 1] = self.INDICATOR_SIMILAR

                        list_2.pop()
                        lineNumbering_2.pop()
                        lineStyling_2.pop()
                        storeNext = True
                    elif listSum[i - 1].startswith("+ "):
                        # Line in text 2 has something added
                        """
                        Line order:
                            - ...
                            + ...
                            ? ...
                        """
                        list_1.pop()
                        lineNumbering_1.pop()
                        lineStyling_1.pop()
                        lineStyling_1[len(lineNumbering_1) - 1] = self.INDICATOR_SIMILAR

                        popIndex_2 = (len(lineNumbering_2) - 1) - 1
                        list_2.pop(popIndex_2)
                        lineNumbering_2.pop(popIndex_2)
                        lineStyling_2.pop()
                        lineStyling_2.pop()
                        lineStyling_2.append(self.INDICATOR_SIMILAR)
            else:
                skipNext = False
        # Display the results
        self.editorPython1.setText("\n".join(list_1))
        self.editorPython2.setText("\n".join(list_2))
        # Set margins and style for both editors
        for i, line in enumerate(lineNumbering_1):
            self._setMarginText(self.editorPython1, i, line)
            lineStyling = lineStyling_1[i]
            if lineStyling != None:
                if lineStyling == self.INDICATOR_SIMILAR:
                    self.editorPython1.markerAdd(i, self._markerSimilar1)
                    self.editorPython1.markerAdd(i, self._markerSimilarSymbol1)
                else:
                    self.editorPython1.markerAdd(i, self._markerUnique1)
                    self.editorPython1.markerAdd(i, self._markerUniqueSymbol1)
        for i, line in enumerate(lineNumbering_2):
            self._setMarginText(self.editorPython2, i, line)
            lineStyling = lineStyling_2[i]
            if lineStyling != None:
                if lineStyling == self.INDICATOR_SIMILAR:
                    self.editorPython2.markerAdd(i, self._markerSimilar2)
                    self.editorPython2.markerAdd(i, self._markerUniqueSymbol2)
                else:
                    self.editorPython2.markerAdd(i, self._markerUnique2)
                    self.editorPython2.markerAdd(i, self._markerUniqueSymbol2)
        # Check if there were any differences
        if (any(lineStyling_1) == False and any(lineStyling_2) == False):
            print ("No difference")
        self._updateMargins()

    def _scnUpdateui(self, scUpdate):
        """Function connected to the SCN_UPDATEUI signal for scroll detection"""
        if self._focusedEditor == self.editorPython1:
            # Scroll the opposite editor
            if scUpdate == _Qsci.QsciScintillaBase.SC_UPDATE_H_SCROLL:
                xOffset = self.editorPython1.SendScintilla(self.GET_X_OFFSET)
                self.editorPython2.SendScintilla(self.SET_X_OFFSET, xOffset)
            elif scUpdate == _Qsci.QsciScintillaBase.SC_UPDATE_V_SCROLL:
                topLine = self.editorPython1.firstVisibleLine()
                self.editorPython2.setFirstVisibleLine(topLine)

        elif self._focusedEditor == self.editorPython2:
            # Scroll the opposite editor
            if scUpdate == _Qsci.QsciScintillaBase.SC_UPDATE_H_SCROLL:
                xOffset = self.editorPython2.SendScintilla(self.GET_X_OFFSET)
                self.editorPython1.SendScintilla(self.SET_X_OFFSET, xOffset)
            elif scUpdate == _Qsci.QsciScintillaBase.SC_UPDATE_V_SCROLL:
                topLine = self.editorPython2.firstVisibleLine()
                self.editorPython1.setFirstVisibleLine(topLine)

    def _cursorChange(self, line, index):
        """
        Function connected to the cursorPositionChanged signal for
        cursor position change detection
        """
        if self._focusedEditor == self.editorPython1:
            # Update the cursor position on the opposite editor
            cursorLine, cursorIndex = self.editorPython1.getCursorPosition()
            # Check if the opposite editor line is long enough
            if self.editorPython2.lineLength(cursorLine) > cursorIndex:
                self.editorPython2.setCursorPosition(cursorLine, cursorIndex)
            else:
                self.editorPython2.setCursorPosition(cursorLine, 0)
            # Update the first visible line, so that the views in both differs match
            currentTopLine = self.editorPython1.firstVisibleLine()
            self.editorPython2.setFirstVisibleLine(currentTopLine)

        elif self._focusedEditor == self.editorPython2:
            # Update the cursor position on the opposite editor
            cursorLine, cursorIndex = self.editorPython2.getCursorPosition()
            # Check if the opposite editor line is long enough
            if self.editorPython1.lineLength(cursorLine) > cursorIndex:
                self.editorPython1.setCursorPosition(cursorLine, cursorIndex)
            else:
                self.editorPython1.setCursorPosition(cursorLine, 0)
            # Update the first visible line, so that the views in both differs match
            currentTopLine = self.editorPython2.firstVisibleLine()
            self.editorPython1.setFirstVisibleLine(currentTopLine)

    def _setMarginText(self, editor, line, text):
        """Set the editor's margin text at the selected line"""
        editor.setMarginText(line, text, self.MARGIN_STYLE)

    def _updateMargins(self):
        """Update the text margin width"""
        self.editorPython1.setMarginWidth(0, "0" * len(str(self.editorPython1.lines())))
        self.editorPython2.setMarginWidth(0, "0" * len(str(self.editorPython2.lines())))


if __name__ == "__main__":
    import sys
    app = _QtWidgets.QApplication(sys.argv)
    editor = TextComparator(r'E:\python\textDifference\test.py')
    editor.show()
    app.exec_()