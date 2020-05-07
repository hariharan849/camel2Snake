import sys, os
sys.path.append(r'E:\python\ExCo-master')

import styleSheet

from PyQt5 import (
    QtGui as _QtGui,
    Qsci as _Qsci
)


class PythonColor:
    TripleDoubleQuotedString = 0xff1a0f0b
    FunctionMethodName = 0xff1a0f0b
    TabsAfterSpaces = 0xff1a0f0b
    Tabs = 0xff1a0f0b
    Decorator = 0xff1a0f0b
    NoWarning = 0xff1a0f0b
    UnclosedString = 0xffe0c0e0
    Spaces = 0xff1a0f0b
    CommentBlock = 0xff1a0f0b
    Comment = 0xff1a0f0b
    TripleSingleQuotedString = 0xff1a0f0b
    SingleQuotedString = 0xff1a0f0b
    Inconsistent = 0xff1a0f0b
    Default = 0xff1a0f0b
    DoubleQuotedString = 0xff1a0f0b
    Operator = 0xff1a0f0b
    Number = 0xff1a0f0b
    Identifier = 0xff1a0f0b
    ClassName = 0xff1a0f0b
    Keyword = 0xff1a0f0b
    HighlightedIdentifier = 0xff1a0f0b
    CustomKeyword = 0xff1a0f0b

class PythonFont:
    ClassName = ('Courier', 0xffb3935c, 10, None)
    Comment = ('Courier', 0xff679d47, 10, None)
    CommentBlock = ('Courier', 0xff7f7f7f, 10, None)
    Decorator = ('Courier', 0xff805000, 10, None)
    Default = ('Courier', 0xfff7f1c1, 10, None)
    DoubleQuotedString = ('Courier', 0xff7ca563, 10, None)
    FunctionMethodName = ('Courier', 0xff6c9686, 10, None)
    HighlightedIdentifier = ('Courier', 0xff407090, 10, None)
    Identifier = ('Courier', 0xfff7f1c1, 10, None)
    Inconsistent = ('Courier', 0xff679d47, 10, None)
    Keyword = ('Courier', 0xff519872, 10, None)
    NoWarning = ('Courier', 0xff808080, 10, None)
    Number = ('Courier', 0xff6c9686, 10, None)
    Operator = ('Courier', 0xfff7f1c1, 10, None)
    SingleQuotedString = ('Courier', 0xff7ca563, 10, None)
    Spaces = ('Courier', 0xff7ca563, 10, None)
    Tabs = ('Courier', 0xff7ca563, 10, None)
    TabsAfterSpaces = ('Courier', 0xff6c9686, 10, None)
    TripleDoubleQuotedString = ('Courier', 0xffe1aa7d, 10, None)
    TripleSingleQuotedString = ('Courier', 0xffe1aa7d, 10, None)
    UnclosedString = ('Courier', 0xfff7f1c1, 10, None)
    CustomKeyword = ('Courier', 0xff6e6e00, 10, True)


class BaseEditor(_Qsci.QsciScintilla):
    ARROW_MARKER_NUM = 8
    def __init__(self, filePath, parent=None):
        super(BaseEditor, self).__init__(parent)

        self._filePath = filePath
        self._font = None

        self._setDefaultFont()
        self._createMargins()
        self._setDefaultProperties()
        self._setLexer()
        self._connectSignals()

        with open(filePath, 'r') as fileObj:
            text = fileObj.read()
        self.setText(text)

        self._setTheme()

    def _setDefaultFont(self):
        self._font = _QtGui.QFont()
        self._font.setFamily('Courier')
        self._font.setFixedPitch(True)
        self._font.setPointSize(10)
        self.setFont(self._font)
        self.setMarginsFont(self._font)

    def _createMargins(self):
        # Margin 0 is used for line numbers
        fontmetrics = _QtGui.QFontMetrics(self._font)
        self.setMarginsFont(self._font)
        self.setMarginWidth(0, fontmetrics.width("00000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(_QtGui.QColor("#cccccc"))

        # Clickable margin 1 for showing markers
        self.setMarginSensitivity(1, True)
        self.markerDefine(_Qsci.QsciScintilla.RightArrow,
                          self.ARROW_MARKER_NUM)
        self.setMarkerBackgroundColor(_QtGui.QColor("#ee1111"),
                                      self.ARROW_MARKER_NUM)

    def _setDefaultProperties(self):
        self.setBraceMatching(_Qsci.QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(_QtGui.QColor("#ffe4e4"))

        self.SendScintilla(
            _Qsci.QsciScintilla.SCI_STYLESETFONT,
            1,
            bytearray(str.encode("Arial"))
        )

        # Hides the horizontal scrollbar at all
        self.SendScintilla(_Qsci.QsciScintilla.SCI_SETHSCROLLBAR, 0)

    def _setLexer(self):
        raise NotImplementedError()

    def _connectSignals(self):
        self.marginClicked.connect(self.onMarginClicked)

    def _setTheme(self):
        self.setFoldMarginColors(
            styleSheet.FoldMargin.ForeGround,
            styleSheet.FoldMargin.BackGround
        )
        self.setMarginsForegroundColor(styleSheet.LineMargin.ForeGround)
        self.setMarginsBackgroundColor(styleSheet.LineMargin.BackGround)
        self.SendScintilla(
            _Qsci.QsciScintillaBase.SCI_STYLESETBACK,
            _Qsci.QsciScintillaBase.STYLE_DEFAULT,
            styleSheet.Paper
        )
        self.SendScintilla(
            _Qsci.QsciScintillaBase.SCI_STYLESETBACK,
            _Qsci.QsciScintillaBase.STYLE_LINENUMBER,
            styleSheet.LineMargin.BackGround
        )
        self.SendScintilla(
            _Qsci.QsciScintillaBase.SCI_SETCARETFORE,
            styleSheet.Cursor
        )
        self.setCaretLineBackgroundColor(
            styleSheet.Cursor_Line_Background
        )

    def onMarginClicked(self):
        raise NotImplementedError()

class SimplePythonEditor(BaseEditor):
    styles = {
        "Default": 0,
        "Comment": 1,
        "Number": 2,
        "DoubleQuotedString": 3,
        "SingleQuotedString": 4,
        "Keyword": 5,
        "TripleSingleQuotedString": 6,
        "TripleDoubleQuotedString": 7,
        "ClassName": 8,
        "FunctionMethodName": 9,
        "Operator": 10,
        "Identifier": 11,
        "CommentBlock": 12,
        "UnclosedString": 13,
        "HighlightedIdentifier": 14,
        "Decorator": 15
    }
    def _setLexer(self):
        lexer = _Qsci.QsciLexerPython()
        lexer.setDefaultFont(_QtGui.QFont('Courier', 10))
        # Set the comment options
        lexer.comment_string = "#"
        # Set the lexer for the current scintilla document
        lexer.setParent(self)
        self.setLexer(lexer)

        for style in self.styles:
            paper = _QtGui.QColor(getattr(PythonColor, style))
            lexer.setPaper(paper, self.styles[style])
            self.setLexerFont(lexer, style, getattr(PythonFont, style))
        # self.setMatchedBraceBackgroundColor(settings.Editor.brace_color)
        self.SendScintilla(_Qsci.QsciScintillaBase.SCI_STYLESETFONT, 1, b'Courier')
        self.setFolding(_Qsci.QsciScintilla.PlainFoldStyle)

    def setLexerFont(self, lexer, styleName, styleOptions):
        font, color, size, bold = styleOptions
        lexer.setColor(
            _QtGui.QColor(color),
            self.styles[styleName]
        )
        weight = _QtGui.QFont.Normal
        if bold == 1 or bold == True:
            weight = _QtGui.QFont.Bold
        elif bold == 2:
            weight = _QtGui.QFont.Black
        lexer.setFont(
            _QtGui.QFont(font, size, weight=weight),
            self.styles[styleName]
        )

    def onMarginClicked(self, nmargin, nline, modifiers):
        # Toggle marker for the line the margin was clicked on
        if self.markersAtLine(nline) != 0:
            self.markerDelete(nline, self.ARROW_MARKER_NUM)
        else:
            self.markerAdd(nline, self.ARROW_MARKER_NUM)

if __name__ == "__main__":
    from PyQt5 import QtWidgets as _QtWidgets
    app = _QtWidgets.QApplication(sys.argv)
    editor = SimplePythonEditor(r'E:\development\sqlite_deploy\_widgets\sales\salesInvoice.py')
    editor.show()
    # editor.setText(open(sys.argv[0]).read())
    app.exec_()