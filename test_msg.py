import clr
clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon, MessageBoxOptions, MessageBoxDefaultButton
try:
    MessageBox.Show("Test", "Test", MessageBoxButtons.OK, MessageBoxIcon.Information, MessageBoxDefaultButton.Button1, MessageBoxOptions.ServiceNotification)
    print("MessageBox works")
except Exception as e:
    print("Error: " + str(e))
