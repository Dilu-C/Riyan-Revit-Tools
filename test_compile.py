import sys
import clr
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')
from System.Windows.Controls import Grid, ColumnDefinition, Button, TextBlock, ComboBox, Border
from System.Windows import Thickness, GridLength, GridUnitType

def test_compile():
    try:
        compile('print("Testing")', '<string>', 'exec')
        return True
    except SyntaxError as e:
        print("Syntax error: " + str(e))
        return False
print("Compilation passed:" + str(test_compile()))
