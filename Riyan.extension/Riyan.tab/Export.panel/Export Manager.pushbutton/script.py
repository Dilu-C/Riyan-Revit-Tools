# -*- coding: utf-8 -*-
import clr
import os
import json
import re

clr.AddReference("PresentationCore")
clr.AddReference("PresentationFramework")
clr.AddReference("System.Xaml")
clr.AddReference("System.Xml")

from System.Windows import Window
from System.IO import StringReader
from System.Xml import XmlReader
from System.Windows.Markup import XamlReader
import System

from pyrevit import revit, DB, UI, forms

doc = revit.doc
uidoc = revit.uidoc

import re

def apply_theme_to_xaml(xaml_str):
    import os
    tab_dir = os.path.dirname(os.path.dirname(__commandpath__))
    logo_path = os.path.join(tab_dir, "About.panel", "About.pushbutton", "logo.png").replace("\\", "/")
    xaml_str = xaml_str.replace("LOGO_PATH", logo_path)

    theme = load_settings().get("theme", "Dark")
    if theme == "Dark":
        return xaml_str

    color_map = {
        "#111111": "#E0E0E0",
        "#121212": "#D4D4D4",
        "#161616": "#D0D0D0",
        "#1A1A1A": "#D4D4D4",
        "#1E1E1E": "#F2F2F2",
        "#0E0E0E": "#D4D4D4",
        "#151515": "#EFEFEF",
        "#1A1215": "#E5E5E5",
        "#1C1410": "#E8E8E8",
        "#2A1C16": "#E0E0E0",
        "#222222": "#B0B0B0",
        "#2A2A2A": "#C8C8C8",
        "#333333": "#A0A0A0",
        "#3A3A3A": "#A5A5A5",
        "#444444": "#888888",
        "#555555": "#888888",
        "#802F2D": "#666666",
        "#9E3A38": "#888888",
        "#661F1D": "#444444",
        "#C0272D": "#FF4444",
        "#5A2020": "#DDDDDD",
        "#FFFFFF": "#111111",
        '"White"': '"#111111"',
        "'White'": "'#111111'",
        "#CCCCCC": "#222222",
        "#888888": "#555555",
        "#666666": "#777777",
        "#C8922A": "#B57B17"
    }

    for k, v in color_map.items():
        if k.startswith("#"):
            xaml_str = re.sub(k, v, xaml_str, flags=re.IGNORECASE)
        else:
            xaml_str = xaml_str.replace(k, v)
    return xaml_str

# ------------------------------------------------------------------------------
# Custom Dark Alert Dialog
# ------------------------------------------------------------------------------
class CustomExportCompletedWindow(object):
    def __init__(self, folder_path, message="Export completed.", theme="Dark"):
        bg = "#111111" if theme == "Dark" else "#F5F5F5"
        border = "#3A3A3A" if theme == "Dark" else "#DDDDDD"
        fg = "#CCCCCC" if theme == "Dark" else "#333333"
        tb_bg = "#1A1A1A" if theme == "Dark" else "#E5E5E5"
        btn_bg = "#2D2D2D" if theme == "Dark" else "#FFFFFF"
        btn_hover = "#3D3D3D" if theme == "Dark" else "#EAEAEA"
        btn_border = "#444444" if theme == "Dark" else "#CCCCCC"
        
        # Adjust height based on number of message lines
        lines_count = len(message.split('\n'))
        win_height = 160 + (lines_count - 1) * 20
        
        xaml_code = """<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Export Manager" Width="360" Height="{win_height}"
        WindowStartupLocation="CenterScreen" 
        Background="Transparent" WindowStyle="None" AllowsTransparency="True"
        ResizeMode="NoResize">
    <Border Background="{bg}" BorderBrush="{border}" BorderThickness="1" CornerRadius="11">
        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="36"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="50"/>
            </Grid.RowDefinitions>

            <!-- TITLE BAR -->
            <Border Grid.Row="0" Background="{tb_bg}" CornerRadius="11,11,0,0">
                <Grid>
                    <TextBlock Text="Export Manager" Foreground="{fg}" FontSize="11" FontWeight="SemiBold" VerticalAlignment="Center" Margin="14,0,0,0"/>
                    <Button x:Name="CloseBtn" Content="&#x2715;" HorizontalAlignment="Right"
                            Width="36" Height="28" BorderThickness="0" Cursor="Hand"
                            Background="Transparent" Foreground="{fg}" Margin="0,0,4,0"
                            FontSize="12">
                        <Button.Style>
                            <Style TargetType="Button">
                                <Setter Property="Template">
                                    <Setter.Value>
                                        <ControlTemplate TargetType="Button">
                                            <Border x:Name="bd" Background="{{TemplateBinding Background}}" CornerRadius="6">
                                                <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                                            </Border>
                                            <ControlTemplate.Triggers>
                                                <Trigger Property="IsMouseOver" Value="True">
                                                    <Setter TargetName="bd" Property="Background" Value="#C0272D"/>
                                                    <Setter Property="Foreground" Value="White"/>
                                                </Trigger>
                                            </ControlTemplate.Triggers>
                                        </ControlTemplate>
                                    </Setter.Value>
                                </Setter>
                            </Style>
                        </Button.Style>
                    </Button>
                </Grid>
            </Border>

            <!-- MESSAGE -->
            <TextBlock Grid.Row="1" Text="{msg}" TextAlignment="Center"
                       Foreground="{fg}" FontSize="13" TextWrapping="Wrap" 
                       HorizontalAlignment="Center" VerticalAlignment="Center" Margin="20"/>

            <!-- FOOTER -->
            <Border Grid.Row="2" Background="{tb_bg}" BorderBrush="{border}" BorderThickness="0,1,0,0" CornerRadius="0,0,11,11">
                <Grid Margin="14,0">
                    <Button x:Name="BtnOpenFolder" Content="Open Folder" 
                            Width="100" Height="30" HorizontalAlignment="Right"
                            Cursor="Hand">
                        <Button.Style>
                            <Style TargetType="Button">
                                <Setter Property="Background" Value="{btn_bg}"/>
                                <Setter Property="Foreground" Value="{fg}"/>
                                <Setter Property="BorderThickness" Value="1"/>
                                <Setter Property="BorderBrush" Value="{btn_border}"/>
                                <Setter Property="Template">
                                    <Setter.Value>
                                        <ControlTemplate TargetType="Button">
                                            <Border x:Name="bd" Background="{{TemplateBinding Background}}" 
                                                     BorderBrush="{{TemplateBinding BorderBrush}}" 
                                                     BorderThickness="{{TemplateBinding BorderThickness}}" CornerRadius="6">
                                                <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                                            </Border>
                                            <ControlTemplate.Triggers>
                                                <Trigger Property="IsMouseOver" Value="True">
                                                    <Setter TargetName="bd" Property="Background" Value="{btn_hover}"/>
                                                </Trigger>
                                            </ControlTemplate.Triggers>
                                        </ControlTemplate>
                                    </Setter.Value>
                                </Setter>
                            </Style>
                        </Button.Style>
                    </Button>
                </Grid>
            </Border>
        </Grid>
    </Border>
</Window>""".format(bg=bg, border=border, fg=fg, tb_bg=tb_bg, btn_bg=btn_bg, btn_hover=btn_hover, btn_border=btn_border, msg=message, win_height=win_height)

        from System.Windows.Markup import XamlReader
        self.win = XamlReader.Parse(xaml_code)
        self.folder_path = folder_path
        
        self.CloseBtn = self.win.FindName("CloseBtn")
        self.BtnOpenFolder = self.win.FindName("BtnOpenFolder")
        
        if self.CloseBtn:
            self.CloseBtn.Click += self.CloseBtn_Click
        if self.BtnOpenFolder:
            self.BtnOpenFolder.Click += self.BtnOpenFolder_Click
            
        self.win.MouseLeftButtonDown += self.TitleBar_MouseDown

    def TitleBar_MouseDown(self, sender, e):
        from System.Windows.Input import MouseButtonState
        if e.LeftButton == MouseButtonState.Pressed:
            self.win.DragMove()

    def CloseBtn_Click(self, sender, e):
        self.win.Close()

    def BtnOpenFolder_Click(self, sender, e):
        import os
        if self.folder_path and os.path.isdir(self.folder_path):
            os.startfile(self.folder_path)
        self.win.Close()
        
    def ShowDialog(self):
        self.win.ShowDialog()

class CustomAlertWindow(object):
    def __init__(self, message, title, icon_char):
        xaml_code = """<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Alert" Width="400" SizeToContent="Height"
        WindowStartupLocation="CenterScreen" 
        Background="#111111" WindowStyle="None" AllowsTransparency="False"
        ResizeMode="NoResize">
    <Border BorderBrush="#3A3A3A" BorderThickness="1">
        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="36"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="46"/>
            </Grid.RowDefinitions>

            <!-- Title Bar -->
            <Grid x:Name="TitleBar" Grid.Row="0" Background="#1A1A1A">
                <StackPanel Orientation="Horizontal" VerticalAlignment="Center" Margin="14,0,0,0">
                    <TextBlock x:Name="TxtAccent" Text="" Foreground="#802F2D" FontSize="13" VerticalAlignment="Center" Margin="0,0,8,0"/>
                    <TextBlock x:Name="TxtTitle" Text="Alert" Foreground="#CCCCCC" FontSize="11" FontWeight="SemiBold" VerticalAlignment="Center"/>
                </StackPanel>
                <Button x:Name="CloseBtn" Content="" HorizontalAlignment="Right"
                        Width="44" Height="36" BorderThickness="0" Cursor="Hand"
                        Background="Transparent" Foreground="#666666"
                        FontSize="12">
                    <Button.Template>
                        <ControlTemplate TargetType="Button">
                            <Border x:Name="bd" Background="{TemplateBinding Background}">
                                <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                            </Border>
                            <ControlTemplate.Triggers>
                                <Trigger Property="IsMouseOver" Value="True">
                                    <Setter TargetName="bd" Property="Background" Value="#C0272D"/>
                                    <Setter Property="Foreground" Value="White"/>
                                </Trigger>
                            </ControlTemplate.Triggers>
                        </ControlTemplate>
                    </Button.Template>
                </Button>
            </Grid>

            <!-- Content Area -->
            <Grid Grid.Row="1" Margin="20,16,20,16">
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="Auto"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>

                <TextBlock x:Name="TxtIcon" Grid.Column="0" Text="" Foreground="#802F2D" FontSize="26" 
                           VerticalAlignment="Center" Margin="0,0,16,0"/>

                <TextBlock x:Name="TxtMessage" Grid.Column="1" Text="" Foreground="#CCCCCC" 
                           FontSize="11.5" TextWrapping="Wrap" VerticalAlignment="Center" HorizontalAlignment="Left"/>
            </Grid>

            <!-- Footer -->
            <Border Grid.Row="2" Background="#0E0E0E" BorderBrush="#222222" BorderThickness="0,1,0,0">
                <Button x:Name="OkBtn" Content="OK" HorizontalAlignment="Right" Width="80" Height="26" 
                        Margin="0,0,14,0" Cursor="Hand" Foreground="White" FontWeight="SemiBold" FontSize="11">
                    <Button.Template>
                        <ControlTemplate TargetType="Button">
                            <Border x:Name="bd" Background="#802F2D" CornerRadius="3">
                                <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                            </Border>
                            <ControlTemplate.Triggers>
                                <Trigger Property="IsMouseOver" Value="True">
                                    <Setter TargetName="bd" Property="Background" Value="#9E3A38"/>
                                </Trigger>
                            </ControlTemplate.Triggers>
                        </ControlTemplate>
                    </Button.Template>
                </Button>
            </Border>
        </Grid>
    </Border>
</Window>
"""
        xaml_code = apply_theme_to_xaml(xaml_code)
        r = XmlReader.Create(StringReader(xaml_code))
        self.win = XamlReader.Load(r)

        self.TxtTitle = self.win.FindName("TxtTitle")
        self.TxtMessage = self.win.FindName("TxtMessage")
        self.TxtIcon = self.win.FindName("TxtIcon")
        self.TxtAccent = self.win.FindName("TxtAccent")
        self.CloseBtn = self.win.FindName("CloseBtn")
        self.OkBtn = self.win.FindName("OkBtn")
        self.TitleBar = self.win.FindName("TitleBar")

        if self.TxtTitle:
            self.TxtTitle.Text = title
        if self.TxtMessage:
            self.TxtMessage.Text = message
        if self.TxtIcon:
            self.TxtIcon.Text = icon_char
        if self.TxtAccent:
            self.TxtAccent.Text = u"\u2B0C"  # â¬Œ
        if self.CloseBtn:
            self.CloseBtn.Content = u"\u2715"  # âœ•
            self.CloseBtn.Click += self.CloseBtn_Click
        if self.OkBtn:
            self.OkBtn.Click += self.OkBtn_Click
        if self.TitleBar:
            self.TitleBar.MouseLeftButtonDown += self.TitleBar_MouseDown

    def TitleBar_MouseDown(self, sender, e):
        try:
            self.win.DragMove()
        except:
            pass

    def MinimizeBtn_Click(self, sender, e):
        import System.Windows
        self.WindowState = System.Windows.WindowState.Minimized

    def MaximizeBtn_Click(self, sender, e):
        import System.Windows
        if self.WindowState == System.Windows.WindowState.Maximized:
            self.WindowState = System.Windows.WindowState.Normal
        else:
            self.WindowState = System.Windows.WindowState.Maximized

    def CloseBtn_Click(self, sender, e):
        self.win.Close()

    def OkBtn_Click(self, sender, e):
        self.win.Close()
    def ShowDialog(self):
        return self.win.ShowDialog()

def show_alert(message, title="Export Manager", is_error=False, is_warning=False):
    icon_char = u"\u2714" # Checkmark
    if is_error:
        icon_char = u"\u2716" # Cross
    elif is_warning:
        icon_char = u"\u26A0" # Warning

    try:
        dialog = CustomAlertWindow(message, title, icon_char)
        dialog.ShowDialog()
    except Exception as e:
        forms.alert("Error rendering UI: " + str(e) + "\n\nOriginal message: " + message, title=title)

# ------------------------------------------------------------------------------
# Custom Alert Window (Hardcoded colors for visibility)
# ------------------------------------------------------------------------------
class CustomAlertWindow(object):
    def __init__(self, message, title, icon_char):
        from System.IO import StringReader
        from System.Xml import XmlReader
        from System.Windows.Markup import XamlReader
        xaml_code = """<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Alert" Width="450" SizeToContent="Height"
        WindowStartupLocation="CenterScreen" 
        Background="#FFFFFF" WindowStyle="None" AllowsTransparency="False"
        ResizeMode="NoResize">
    <Border BorderBrush="#CCCCCC" BorderThickness="1">
        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="36"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="46"/>
            </Grid.RowDefinitions>

            <!-- Title Bar -->
            <Grid x:Name="TitleBar" Grid.Row="0" Background="#F0F0F0">
                <StackPanel Orientation="Horizontal" VerticalAlignment="Center" Margin="14,0,0,0">
                    <TextBlock Text="{}" Foreground="#333333" FontSize="12" FontWeight="SemiBold" VerticalAlignment="Center"/>
                </StackPanel>
                <Button x:Name="CloseBtn" Content="X" HorizontalAlignment="Right" Width="44" Height="36" BorderThickness="0" Background="Transparent" Foreground="#666666" FontSize="12" Cursor="Hand"/>
            </Grid>

            <!-- Content Area -->
            <Grid Grid.Row="1" Margin="20,20,20,20">
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="Auto"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>
                <TextBlock Grid.Column="0" Text="{}" Foreground="#D32F2F" FontSize="26" VerticalAlignment="Center" Margin="0,0,16,0"/>
                <TextBlock Grid.Column="1" Text="{}" Foreground="#111111" FontSize="12" TextWrapping="Wrap" VerticalAlignment="Center" HorizontalAlignment="Left"/>
            </Grid>

            <!-- Footer -->
            <Border Grid.Row="2" Background="#F5F5F5" BorderBrush="#E0E0E0" BorderThickness="0,1,0,0">
                <Button x:Name="OkBtn" Content="OK" HorizontalAlignment="Right" Width="80" Height="26" Margin="0,0,14,0" Cursor="Hand" Background="#2196F3" Foreground="White" FontWeight="SemiBold" FontSize="11"/>
            </Border>
        </Grid>
    </Border>
</Window>
""".format(title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), 
           icon_char, 
           message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        
        r = XmlReader.Create(StringReader(xaml_code))
        self.win = XamlReader.Load(r)
        
        self.CloseBtn = self.win.FindName("CloseBtn")
        self.OkBtn = self.win.FindName("OkBtn")
        self.TitleBar = self.win.FindName("TitleBar")
        
        if self.CloseBtn:
            self.CloseBtn.Click += self.close_window
        if self.OkBtn:
            self.OkBtn.Click += self.close_window
        if self.TitleBar:
            self.TitleBar.MouseLeftButtonDown += self.drag_window

    def drag_window(self, sender, e):
        try:
            self.win.DragMove()
        except:
            pass

    def close_window(self, sender, e):
        self.win.Close()

    def ShowDialog(self):
        self.win.ShowDialog()

# ------------------------------------------------------------------------------
# Custom Dark Text Input Dialog
# ------------------------------------------------------------------------------
class CustomTextInputWindow(object):
    def __init__(self, title, description, default_value=""):
        self.result = None
        xaml_code = """<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Input" Width="400" SizeToContent="Height"
        WindowStartupLocation="CenterScreen"
        Background="#111111" WindowStyle="None" AllowsTransparency="False"
        ResizeMode="NoResize">
    <Border BorderBrush="#3A3A3A" BorderThickness="1">
        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="36"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="46"/>
            </Grid.RowDefinitions>

            <!-- Title Bar -->
            <Grid x:Name="TitleBar" Grid.Row="0" Background="#1A1A1A">
                <StackPanel Orientation="Horizontal" VerticalAlignment="Center" Margin="14,0,0,0">
                    <TextBlock x:Name="TxtAccent" Text="" Foreground="#802F2D" FontSize="13" VerticalAlignment="Center" Margin="0,0,8,0"/>
                    <TextBlock x:Name="TxtTitle" Text="Input" Foreground="#CCCCCC" FontSize="11" FontWeight="SemiBold" VerticalAlignment="Center"/>
                </StackPanel>
                <Button x:Name="CloseBtn" Content="" HorizontalAlignment="Right"
                        Width="44" Height="36" BorderThickness="0" Cursor="Hand"
                        Background="Transparent" Foreground="#666666"
                        FontSize="12">
                    <Button.Template>
                        <ControlTemplate TargetType="Button">
                            <Border x:Name="bd" Background="{TemplateBinding Background}">
                                <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                            </Border>
                            <ControlTemplate.Triggers>
                                <Trigger Property="IsMouseOver" Value="True">
                                    <Setter TargetName="bd" Property="Background" Value="#C0272D"/>
                                    <Setter Property="Foreground" Value="White"/>
                                </Trigger>
                            </ControlTemplate.Triggers>
                        </ControlTemplate>
                    </Button.Template>
                </Button>
            </Grid>

            <!-- Content Area -->
            <StackPanel Grid.Row="1" Margin="20,16,20,16">
                <TextBlock x:Name="TxtDescription" Text="Enter value:" Foreground="#CCCCCC" FontSize="11.5" Margin="0,0,0,8"/>
                <TextBox x:Name="TxtInput" Background="#161616" Foreground="White" BorderBrush="#333333" BorderThickness="1" Padding="6,4" FontSize="12"/>
            </StackPanel>

            <!-- Footer -->
            <Border Grid.Row="2" Background="#0E0E0E" BorderBrush="#222222" BorderThickness="0,1,0,0">
                <StackPanel Orientation="Horizontal" HorizontalAlignment="Right">
                    <Button x:Name="CancelBtn" Content="Cancel" Width="80" Height="26" Margin="0,0,8,0" Cursor="Hand" Foreground="#AAAAAA" FontSize="11">
                        <Button.Template>
                            <ControlTemplate TargetType="Button">
                                <Border x:Name="bd" Background="#222222" CornerRadius="3">
                                    <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                                </Border>
                                <ControlTemplate.Triggers>
                                    <Trigger Property="IsMouseOver" Value="True">
                                        <Setter TargetName="bd" Property="Background" Value="#333333"/>
                                    </Trigger>
                                </ControlTemplate.Triggers>
                            </ControlTemplate>
                        </Button.Template>
                    </Button>
                    <Button x:Name="OkBtn" Content="OK" Width="80" Height="26" Margin="0,0,14,0" Cursor="Hand" Foreground="White" FontWeight="SemiBold" FontSize="11">
                        <Button.Template>
                            <ControlTemplate TargetType="Button">
                                <Border x:Name="bd" Background="#802F2D" CornerRadius="3">
                                    <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                                </Border>
                                <ControlTemplate.Triggers>
                                    <Trigger Property="IsMouseOver" Value="True">
                                        <Setter TargetName="bd" Property="Background" Value="#9E3A38"/>
                                    </Trigger>
                                </ControlTemplate.Triggers>
                            </ControlTemplate>
                        </Button.Template>
                    </Button>
                </StackPanel>
            </Border>
        </Grid>
    </Border>
</Window>
"""
        xaml_code = apply_theme_to_xaml(xaml_code)
        r = XmlReader.Create(StringReader(xaml_code))
        self.win = XamlReader.Load(r)

        self.TxtTitle = self.win.FindName("TxtTitle")
        self.TxtDescription = self.win.FindName("TxtDescription")
        self.TxtInput = self.win.FindName("TxtInput")
        self.TxtAccent = self.win.FindName("TxtAccent")
        self.CloseBtn = self.win.FindName("CloseBtn")
        self.OkBtn = self.win.FindName("OkBtn")
        self.CancelBtn = self.win.FindName("CancelBtn")
        self.TitleBar = self.win.FindName("TitleBar")

        if self.TxtTitle:
            self.TxtTitle.Text = title
        if self.TxtDescription:
            self.TxtDescription.Text = description
        if self.TxtInput and default_value:
            self.TxtInput.Text = default_value
            self.TxtInput.SelectAll()
            
        theme = load_settings().get("theme", "Dark")
        if theme != "Dark" and self.TxtInput:
            import System.Windows.Media
            self.TxtInput.Foreground = System.Windows.Media.Brushes.Black
            self.TxtInput.Background = System.Windows.Media.Brushes.White
        if self.TxtAccent:
            self.TxtAccent.Text = u"\u2B0C"  # â¬Œ
        if self.CloseBtn:
            self.CloseBtn.Content = u"\u2715"  # âœ•
            self.CloseBtn.Click += self.CloseBtn_Click
        if self.CancelBtn:
            self.CancelBtn.Click += self.CancelBtn_Click
        if self.OkBtn:
            self.OkBtn.Click += self.OkBtn_Click
        if self.TitleBar:
            self.TitleBar.MouseLeftButtonDown += self.TitleBar_MouseDown

        # Focus textbox
        if self.TxtInput:
            self.TxtInput.Focus()

    def TitleBar_MouseDown(self, sender, e):
        try:
            self.win.DragMove()
        except:
            pass

    def MinimizeBtn_Click(self, sender, e):
        import System.Windows
        self.WindowState = System.Windows.WindowState.Minimized

    def MaximizeBtn_Click(self, sender, e):
        import System.Windows
        if self.WindowState == System.Windows.WindowState.Maximized:
            self.WindowState = System.Windows.WindowState.Normal
        else:
            self.WindowState = System.Windows.WindowState.Maximized

    def CloseBtn_Click(self, sender, e):
        self.result = None
        self.win.Close()

    def CancelBtn_Click(self, sender, e):
        self.result = None
        self.win.Close()

    def OkBtn_Click(self, sender, e):
        if self.TxtInput:
            self.result = self.TxtInput.Text
        self.win.Close()

    def ShowDialog(self):
        self.win.ShowDialog()
        return self.result

# ------------------------------------------------------------------------------
# Custom Profile Save Dialog
# ------------------------------------------------------------------------------
class CustomProfileSaveWindow(object):
    def __init__(self):
        self.result = None
        xaml_code = """<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Save Profile" Width="360" SizeToContent="Height"
        WindowStartupLocation="CenterScreen" 
        Background="#111111" WindowStyle="None" AllowsTransparency="False"
        ResizeMode="NoResize">
    <Border BorderBrush="#3A3A3A" BorderThickness="1">
        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="36"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="46"/>
            </Grid.RowDefinitions>

            <!-- Title Bar -->
            <Grid x:Name="TitleBar" Grid.Row="0" Background="#1A1A1A">
                <StackPanel Orientation="Horizontal" VerticalAlignment="Center" Margin="14,0,0,0">
                    <TextBlock x:Name="TxtAccent" Text="" Foreground="#802F2D" FontSize="13" VerticalAlignment="Center" Margin="0,0,8,0"/>
                    <TextBlock x:Name="TxtTitle" Text="Save Profile" Foreground="#CCCCCC" FontSize="11" FontWeight="SemiBold" VerticalAlignment="Center"/>
                </StackPanel>
                <Button x:Name="CloseBtn" Content="" HorizontalAlignment="Right"
                        Width="44" Height="36" BorderThickness="0" Cursor="Hand"
                        Background="Transparent" Foreground="#666666"
                        FontSize="12">
                    <Button.Template>
                        <ControlTemplate TargetType="Button">
                            <Border x:Name="bd" Background="{TemplateBinding Background}">
                                <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                            </Border>
                            <ControlTemplate.Triggers>
                                <Trigger Property="IsMouseOver" Value="True">
                                    <Setter TargetName="bd" Property="Background" Value="#C0272D"/>
                                    <Setter Property="Foreground" Value="White"/>
                                </Trigger>
                            </ControlTemplate.Triggers>
                        </ControlTemplate>
                    </Button.Template>
                </Button>
            </Grid>

            <!-- Content Area -->
            <StackPanel Grid.Row="1" Margin="20,16,20,16">
                <TextBlock Text="This profile will be updated with" Foreground="#CCCCCC" FontSize="11.5" Margin="0,0,0,12"/>
                <TextBlock Text="- Custom Drawing Number" Foreground="#888888" FontSize="11.5" Margin="0,0,0,4"/>
                <TextBlock Text="- Format options" Foreground="#888888" FontSize="11.5" Margin="0,0,0,4"/>
                <TextBlock Text="  PDF, DWG, DGN, DWF/DWFx, NWC, IFC AND IMG" Foreground="#888888" FontSize="11" Margin="0,0,0,8" TextWrapping="Wrap"/>
            </StackPanel>

            <!-- Footer -->
            <Border Grid.Row="2" Background="#0E0E0E" BorderBrush="#222222" BorderThickness="0,1,0,0">
                <StackPanel Orientation="Horizontal" HorizontalAlignment="Right">
                    <Button x:Name="SaveAsBtn" Content="Save As" Width="80" Height="26" Margin="0,0,8,0" Cursor="Hand" Foreground="#AAAAAA" FontSize="11">
                        <Button.Template>
                            <ControlTemplate TargetType="Button">
                                <Border x:Name="bd" Background="#222222" CornerRadius="3">
                                    <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                                </Border>
                                <ControlTemplate.Triggers>
                                    <Trigger Property="IsMouseOver" Value="True">
                                        <Setter TargetName="bd" Property="Background" Value="#333333"/>
                                    </Trigger>
                                </ControlTemplate.Triggers>
                            </ControlTemplate>
                        </Button.Template>
                    </Button>
                    <Button x:Name="SaveBtn" Content="Save" Width="80" Height="26" Margin="0,0,14,0" Cursor="Hand" Foreground="White" FontWeight="SemiBold" FontSize="11">
                        <Button.Template>
                            <ControlTemplate TargetType="Button">
                                <Border x:Name="bd" Background="#802F2D" CornerRadius="3">
                                    <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                                </Border>
                                <ControlTemplate.Triggers>
                                    <Trigger Property="IsMouseOver" Value="True">
                                        <Setter TargetName="bd" Property="Background" Value="#9E3A38"/>
                                    </Trigger>
                                </ControlTemplate.Triggers>
                            </ControlTemplate>
                        </Button.Template>
                    </Button>
                </StackPanel>
            </Border>
        </Grid>
    </Border>
</Window>
"""
        xaml_code = apply_theme_to_xaml(xaml_code)
        r = XmlReader.Create(StringReader(xaml_code))
        self.win = XamlReader.Load(r)

        self.TxtAccent = self.win.FindName("TxtAccent")
        self.CloseBtn = self.win.FindName("CloseBtn")
        self.SaveAsBtn = self.win.FindName("SaveAsBtn")
        self.SaveBtn = self.win.FindName("SaveBtn")
        self.TitleBar = self.win.FindName("TitleBar")

        if self.TxtAccent:
            self.TxtAccent.Text = u"\u2B0C"  # â¬Œ
        if self.CloseBtn:
            self.CloseBtn.Content = u"\u2715"  # âœ•
            self.CloseBtn.Click += self.CloseBtn_Click
        if self.SaveAsBtn:
            self.SaveAsBtn.Click += self.SaveAsBtn_Click
        if self.SaveBtn:
            self.SaveBtn.Click += self.SaveBtn_Click
        if self.TitleBar:
            self.TitleBar.MouseLeftButtonDown += self.TitleBar_MouseDown

    def TitleBar_MouseDown(self, sender, e):
        try:
            self.win.DragMove()
        except:
            pass

    def MinimizeBtn_Click(self, sender, e):
        import System.Windows
        self.WindowState = System.Windows.WindowState.Minimized

    def MaximizeBtn_Click(self, sender, e):
        import System.Windows
        if self.WindowState == System.Windows.WindowState.Maximized:
            self.WindowState = System.Windows.WindowState.Normal
        else:
            self.WindowState = System.Windows.WindowState.Maximized

    def CloseBtn_Click(self, sender, e):
        self.result = "Cancel"
        self.win.Close()

    def SaveAsBtn_Click(self, sender, e):
        self.result = "SaveAs"
        self.win.Close()

    def SaveBtn_Click(self, sender, e):
        self.result = "Save"
        self.win.Close()

    def ShowDialog(self):
        self.win.ShowDialog()
        return self.result

def show_text_input(title, description, default_value=""):
    try:
        dialog = CustomTextInputWindow(title, description, default_value)
        return dialog.ShowDialog()
    except Exception as e:
        show_alert("Dialog Error: " + str(e), is_error=True)
        from rpw.ui.forms import TextInput
        return TextInput(title, description=description)

# ------------------------------------------------------------------------------
# Settings Storage Utility
# ------------------------------------------------------------------------------
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "naming_settings.json")

def load_settings():
    default_settings = {
        "active_scheme": "Default",
        "schemes": {
            "Default": [
                {"ParameterName": "Sheet Number", "Prefix": "", "Suffix": "", "Separator": " - "},
                {"ParameterName": "Sheet Name", "Prefix": "", "Suffix": "", "Separator": ""}
            ]
        },
        "profile_settings": {},
        "view_sets": {},
        "export_options": {
            "temp_hide_off": True,
            "worksharing_off": True,
            "reveal_hidden_off": True,
            "reveal_constraints_off": True
        }
    }
    if not os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(default_settings, f, indent=4)
        except Exception:
            pass
        return default_settings

    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            if "schemes" not in data or not data["schemes"]:
                data["schemes"] = default_settings["schemes"]
                data["active_scheme"] = default_settings["active_scheme"]
            if "view_sets" not in data:
                data["view_sets"] = {}
            if "profile_settings" not in data:
                data["profile_settings"] = {}
            if "export_options" not in data:
                data["export_options"] = default_settings["export_options"]
            return data
    except Exception:
        return default_settings

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        show_alert("Error saving naming settings:\n" + str(e), is_error=True)

# ------------------------------------------------------------------------------
# View Models
# ------------------------------------------------------------------------------
class SheetViewModel(object):
    def __init__(self, sheet, scheme_parts, doc, is_view=False):
        self.Sheet = sheet
        self.is_view = is_view

        if is_view:
            self.SheetNumber = str(sheet.ViewType)
            self.SheetName = sheet.Name
            self.Revision = "-"
            self.Size = "-"
        else:
            self.SheetNumber = sheet.SheetNumber
            self.SheetName = sheet.Name

            # Get revision
            p = sheet.get_Parameter(DB.BuiltInParameter.SHEET_CURRENT_REVISION)
            self.Revision = p.AsString() or p.AsValueString() or "-" if p else "-"

            # Get Size (from TitleBlock if available)
            self.Size = ""
            try:
                tbs = DB.FilteredElementCollector(doc, sheet.Id).OfCategory(DB.BuiltInCategory.OST_TitleBlocks).ToElements()
                if tbs:
                    self.Size = tbs[0].Name
                else:
                    self.Size = "A1"
            except:
                self.Size = "A1"

        self._is_selected = False
        self._custom_file_name = ""
        self.update_filename(scheme_parts, doc)

    @property
    def IsSelected(self):
        return self._is_selected

    @IsSelected.setter
    def IsSelected(self, value):
        self._is_selected = value

    @property
    def CustomFileName(self):
        return self._custom_file_name

    @CustomFileName.setter
    def CustomFileName(self, value):
        self._custom_file_name = value

    def update_filename(self, scheme_parts, doc):
        self.CustomFileName = generate_filename(self.Sheet, scheme_parts, doc)

class QueueItemViewModel(object):
    def __init__(self, sheet_vm, format, active_scheme_parts, doc):
        self.SheetVM = sheet_vm
        self.SheetNumber = sheet_vm.SheetNumber
        self.SheetName = sheet_vm.SheetName
        self.Format = format
        self.TargetFileName = generate_filename(sheet_vm.Sheet, active_scheme_parts, doc)
        self._status = "Pending"

    @property
    def Status(self):
        return self._status

    @Status.setter
    def Status(self, value):
        self._status = value

class ParameterViewModel(object):
    def __init__(self, name, category):
        self._name = name
        self._category = category

    @property
    def Name(self):
        return self._name

    @property
    def Category(self):
        return self._category

class NamingPart(object):
    def __init__(self, param_name, sample_value="", prefix="", suffix="", separator=""):
        self._param_name = param_name
        self._sample_value = sample_value
        self._prefix = prefix
        self._suffix = suffix
        self._separator = separator

    @property
    def ParameterName(self):
        return self._param_name

    @property
    def SampleValue(self):
        return self._sample_value

    @property
    def Prefix(self):
        return self._prefix

    @Prefix.setter
    def Prefix(self, value):
        self._prefix = value or ""

    @property
    def Suffix(self):
        return self._suffix

    @Suffix.setter
    def Suffix(self, value):
        self._suffix = value or ""

    @property
    def Separator(self):
        return self._separator

    @Separator.setter
    def Separator(self, value):
        self._separator = value or ""

    def to_dict(self):
        return {
            "ParameterName": self._param_name,
            "Prefix": self._prefix,
            "Suffix": self._suffix,
            "Separator": self._separator
        }

# ------------------------------------------------------------------------------
# Parameter and Sample Value Helpers
# ------------------------------------------------------------------------------
def get_sample_value(doc, param_name, sheet=None):
    if sheet:
        p = sheet.LookupParameter(param_name)
        if not p:
            for bp in sheet.Parameters:
                if bp.Definition.Name == param_name:
                    p = bp
                    break
        if p:
            val = p.AsValueString() or p.AsString()
            if val is not None:
                return val

    proj_info = doc.ProjectInformation
    if proj_info:
        p = proj_info.LookupParameter(param_name)
        if not p:
            for bp in proj_info.Parameters:
                if bp.Definition.Name == param_name:
                    p = bp
                    break
        if p:
            val = p.AsValueString() or p.AsString()
            if val is not None:
                return val

    # Fallback default values
    if param_name == "Sheet Number": return "A101"
    if param_name == "Sheet Name": return "Floor Plan"
    if param_name == "Current Revision": return "01"
    if param_name == "Discipline": return "Architectural"
    return param_name

def get_all_sheet_parameters(doc):
    params = []
    seen = set()

    # 1. Sheet Category Parameters
    sheets = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Sheets).WhereElementIsNotElementType().ToElements()
    if sheets:
        sheet = sheets[0]
        for p in sheet.Parameters:
            name = p.Definition.Name
            if name and name not in seen:
                seen.add(name)
                params.append(ParameterViewModel(name, "Sheet"))

    # 2. Project Information Parameters
    proj_info = doc.ProjectInformation
    if proj_info:
        for p in proj_info.Parameters:
            name = p.Definition.Name
            if name and name not in seen:
                seen.add(name)
                params.append(ParameterViewModel(name, "Project Information"))

    # Fallbacks for core parameters
    for name, cat in [("Sheet Number", "Sheet"), ("Sheet Name", "Sheet"), ("Current Revision", "Sheet")]:
        if name not in seen:
            seen.add(name)
            params.append(ParameterViewModel(name, cat))

    return sorted(params, key=lambda x: x.Name)

def generate_filename(sheet, scheme_parts, doc):
    name_parts = []
    for part in scheme_parts:
        param_name = part["ParameterName"]
        prefix = part.get("Prefix", "")
        suffix = part.get("Suffix", "")
        separator = part.get("Separator", "")

        val = ""
        p = sheet.LookupParameter(param_name)
        if not p:
            for bp in sheet.Parameters:
                if bp.Definition.Name == param_name:
                    p = bp
                    break
        if p:
            val = p.AsValueString() or p.AsString() or ""

        if not val and doc.ProjectInformation:
            pi_p = doc.ProjectInformation.LookupParameter(param_name)
            if not pi_p:
                for bp in doc.ProjectInformation.Parameters:
                    if bp.Definition.Name == param_name:
                        pi_p = bp
                        break
            if pi_p:
                val = pi_p.AsValueString() or pi_p.AsString() or ""

        name_parts.append(prefix + val + suffix + separator)

    filename = "".join(name_parts)

    # Clean invalid characters
    invalid_chars = '<>:"/\\|?*'
    for c in invalid_chars:
        filename = filename.replace(c, "_")

    # Final fallback if name resolves to empty string
    filename = filename.strip()
    if not filename:
        try:
            filename = sheet.SheetNumber + " - " + sheet.Name
        except AttributeError:
            filename = str(sheet.ViewType) + " - " + sheet.Name

    return filename

def get_project_info_parameters(doc):
    params = []
    seen = set()
    proj_info = doc.ProjectInformation
    if proj_info:
        for p in proj_info.Parameters:
            name = p.Definition.Name
            if name and name not in seen:
                seen.add(name)
                params.append(ParameterViewModel(name, "Project Information"))
    return sorted(params, key=lambda x: x.Name)

# ------------------------------------------------------------------------------
# Naming Builder Form Controller
# ------------------------------------------------------------------------------
class NamingBuilderForm(forms.WPFWindow):
    def __init__(self, xaml_file_name, current_scheme_name, doc, sheets, is_combined=False):
        forms.WPFWindow.__init__(self, xaml_file_name)
        self.doc = doc
        self.sheets = sheets
        self.is_combined = is_combined
        self.sample_sheet = sheets[0] if sheets else None

        # Load settings
        self.settings = load_settings()
        self.current_scheme_name = current_scheme_name

        target_dict = self.settings.get("combined_schemes", {}) if is_combined else self.settings.get("schemes", {})

        if self.current_scheme_name not in target_dict:
            if is_combined:
                self.current_scheme_name = self.settings.get("active_combined_scheme", "Default")
                if self.current_scheme_name not in target_dict and target_dict:
                    self.current_scheme_name = list(target_dict.keys())[0]
            else:
                self.current_scheme_name = self.settings.get("active_scheme", "Default")
                if self.current_scheme_name not in target_dict and target_dict:
                    self.current_scheme_name = list(target_dict.keys())[0]

        self.TxtSchemeName.Text = self.current_scheme_name

        # Populate available parameters
        if is_combined:
            self.all_params = get_project_info_parameters(doc)
        else:
            self.all_params = get_all_sheet_parameters(doc)

        # Initialize selected parameters list
        self.selected_parts = []
        scheme_data = target_dict.get(self.current_scheme_name, [])
        for item in scheme_data:
            param_name = item["ParameterName"]
            prefix = item.get("Prefix", "")
            suffix = item.get("Suffix", "")
            separator = item.get("Separator", "")
            sample_val = get_sample_value(doc, param_name, None if is_combined else self.sample_sheet)
            self.selected_parts.append(NamingPart(param_name, sample_val, prefix, suffix, separator))

        self.GridSelectedParams.ItemsSource = self.selected_parts

        self.CmbCategory.SelectedIndex = 0
        self.filter_parameters()
        self.update_preview()
        
        self.LstAvailableParams.PreviewMouseDoubleClick += self.LstAvailableParams_MouseDoubleClick
        self.GridSelectedParams.PreviewMouseDoubleClick += self.GridSelectedParams_MouseDoubleClick

    def refresh_selected_parts(self):
        new_list = [x for x in self.selected_parts]
        self.GridSelectedParams.ItemsSource = None
        self.GridSelectedParams.ItemsSource = new_list
        self.selected_parts = new_list
        self.update_preview()

    def TitleBar_MouseDown(self, sender, e):
        try:
            self.DragMove()
        except:
            pass

    def MinimizeBtn_Click(self, sender, e):
        import System.Windows
        self.WindowState = System.Windows.WindowState.Minimized

    def MaximizeBtn_Click(self, sender, e):
        import System.Windows
        if self.WindowState == System.Windows.WindowState.Maximized:
            self.WindowState = System.Windows.WindowState.Normal
        else:
            self.WindowState = System.Windows.WindowState.Maximized

    def CloseBtn_Click(self, sender, e):
        self.DialogResult = False
        self.Close()

    def filter_parameters(self):
        if not hasattr(self, 'LstAvailableParams'):
            return

        search_text = self.TxtSearch.Text.lower().strip()
        cat_idx = self.CmbCategory.SelectedIndex

        filtered = []
        for p in self.all_params:
            if cat_idx == 1 and p.Category != "Sheet":
                continue
            if cat_idx == 2 and p.Category != "Project Information":
                continue

            if search_text and search_text not in p.Name.lower():
                continue

            filtered.append(p)

        self.LstAvailableParams.ItemsSource = filtered

    def TxtSearch_TextChanged(self, sender, e):
        self.filter_parameters()

    def CmbCategory_SelectionChanged(self, sender, e):
        self.filter_parameters()

    def BtnAdd_Click(self, sender, e):
        selected_item = self.LstAvailableParams.SelectedItem
        if selected_item:
            param_name = selected_item.Name
            sample_val = get_sample_value(self.doc, param_name, None if self.is_combined else self.sample_sheet)
            part = NamingPart(param_name, sample_val, "", "", "")
            self.selected_parts.append(part)
            self.refresh_selected_parts()

    def LstAvailableParams_MouseDoubleClick(self, sender, e):
        self.BtnAdd_Click(sender, e)

    def BtnRemove_Click(self, sender, e):
        selected_item = self.GridSelectedParams.SelectedItem
        if selected_item:
            self.selected_parts.remove(selected_item)
            self.refresh_selected_parts()

    def GridSelectedParams_MouseDoubleClick(self, sender, e):
        self.BtnRemove_Click(sender, e)

    def BtnMoveToTop_Click(self, sender, e):
        selected_item = self.GridSelectedParams.SelectedItem
        if selected_item:
            idx = self.selected_parts.index(selected_item)
            if idx > 0:
                self.selected_parts.remove(selected_item)
                self.selected_parts.insert(0, selected_item)
                self.refresh_selected_parts()
                self.GridSelectedParams.SelectedItem = selected_item

    def BtnMoveUp_Click(self, sender, e):
        selected_item = self.GridSelectedParams.SelectedItem
        if selected_item:
            idx = self.selected_parts.index(selected_item)
            if idx > 0:
                self.selected_parts.remove(selected_item)
                self.selected_parts.insert(idx - 1, selected_item)
                self.refresh_selected_parts()
                self.GridSelectedParams.SelectedItem = selected_item

    def BtnMoveDown_Click(self, sender, e):
        selected_item = self.GridSelectedParams.SelectedItem
        if selected_item:
            idx = self.selected_parts.index(selected_item)
            if idx < len(self.selected_parts) - 1:
                self.selected_parts.remove(selected_item)
                self.selected_parts.insert(idx + 1, selected_item)
                self.refresh_selected_parts()
                self.GridSelectedParams.SelectedItem = selected_item

    def BtnMoveToBottom_Click(self, sender, e):
        selected_item = self.GridSelectedParams.SelectedItem
        if selected_item:
            idx = self.selected_parts.index(selected_item)
            if idx < len(self.selected_parts) - 1:
                self.selected_parts.remove(selected_item)
                self.selected_parts.append(selected_item)
                self.refresh_selected_parts()
                self.GridSelectedParams.SelectedItem = selected_item

    def BtnReset_Click(self, sender, e):
        self.selected_parts = []
        self.refresh_selected_parts()

    def GridSelectedParams_CellEditEnding(self, sender, e):
        from System.Windows.Threading import DispatcherPriority
        from System import Action
        self.Dispatcher.BeginInvoke(Action(self.update_preview), DispatcherPriority.Background)

    def update_preview(self):
        preview_parts = []
        for part in self.selected_parts:
            val = part.SampleValue or ""
            prefix = part.Prefix or ""
            suffix = part.Suffix or ""
            separator = part.Separator or ""
            preview_parts.append(prefix + val + suffix + separator)

        preview_text = "".join(preview_parts)
        if not preview_text:
            preview_text = "[None]"
        self.TxtPreview.Text = preview_text

    def BtnSaveScheme_Click(self, sender, e):
        scheme_name = self.TxtSchemeName.Text.strip()
        if not scheme_name:
            show_alert("Please enter a valid scheme name.", is_warning=True)
            return

        serialized = [part.to_dict() for part in self.selected_parts]

        target_dict = "combined_schemes" if getattr(self, "is_combined", False) else "schemes"
        target_active = "active_combined_scheme" if getattr(self, "is_combined", False) else "active_scheme"

        if target_dict not in self.settings:
            self.settings[target_dict] = {}

        self.settings[target_dict][scheme_name] = serialized
        self.settings[target_active] = scheme_name
        save_settings(self.settings)

        self.current_scheme_name = scheme_name
        show_alert("Scheme '{}' saved successfully!".format(scheme_name))

    def BtnDeleteScheme_Click(self, sender, e):
        scheme_name = self.TxtSchemeName.Text.strip()

        target_dict = "combined_schemes" if getattr(self, "is_combined", False) else "schemes"
        target_active = "active_combined_scheme" if getattr(self, "is_combined", False) else "active_scheme"

        if target_dict not in self.settings or scheme_name not in self.settings[target_dict]:
            show_alert("Scheme '{}' does not exist.".format(scheme_name), is_warning=True)
            return

        if len(self.settings[target_dict]) <= 1:
            show_alert("Cannot delete the only naming scheme. At least one scheme must exist.", is_warning=True)
            return

        del self.settings[target_dict][scheme_name]

        new_active = list(self.settings[target_dict].keys())[0]
        self.settings[target_active] = new_active
        save_settings(self.settings)

        show_alert("Scheme '{}' deleted.".format(scheme_name))

        self.current_scheme_name = new_active
        self.TxtSchemeName.Text = new_active
        self.selected_parts = []
        for item in self.settings[target_dict][new_active]:
            param_name = item["ParameterName"]
            prefix = item.get("Prefix", "")
            suffix = item.get("Suffix", "")
            separator = item.get("Separator", "")
            sample_val = get_sample_value(self.doc, param_name, None if getattr(self, "is_combined", False) else self.sample_sheet)
            self.selected_parts.append(NamingPart(param_name, sample_val, prefix, suffix, separator))

        self.GridSelectedParams.ItemsSource = None
        self.GridSelectedParams.ItemsSource = self.selected_parts
        self.update_preview()

    def BtnCancel_Click(self, sender, e):
        self.DialogResult = False
        self.Close()

    def BtnOk_Click(self, sender, e):
        scheme_name = self.TxtSchemeName.Text.strip()
        if not scheme_name:
            show_alert("Please enter a valid scheme name.", is_warning=True)
            return

        serialized = [part.to_dict() for part in self.selected_parts]

        target_dict = "combined_schemes" if getattr(self, "is_combined", False) else "schemes"
        target_active = "active_combined_scheme" if getattr(self, "is_combined", False) else "active_scheme"

        if target_dict not in self.settings:
            self.settings[target_dict] = {}

        self.settings[target_dict][scheme_name] = serialized
        self.settings[target_active] = scheme_name
        save_settings(self.settings)

        self.DialogResult = True
        self.Close()

# ------------------------------------------------------------------------------
# Create Profile Dialog
# ------------------------------------------------------------------------------
class CreateProfileDialog(object):
    def __init__(self, current_scheme_name, settings):
        self.result_name = None
        self.result_rules = None
        self._current_scheme_name = current_scheme_name
        self._settings = settings

        theme = settings.get("theme", "Dark")
        bg = "#1E1E1E" if theme == "Dark" else "#F5F5F5"
        fg = "#FFFFFF" if theme == "Dark" else "#111111"
        border_color = "#333333" if theme == "Dark" else "#CCCCCC"
        input_bg = "#2A2A2A" if theme == "Dark" else "#FFFFFF"
        btn_bg = "#C0272D"

        xaml_str = (
            u'<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"'
            u' xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"'
            u' Title="Create Profile" Width="340" SizeToContent="Height"'
            u' WindowStartupLocation="CenterScreen" ResizeMode="NoResize"'
            u' Background="' + bg + u'">'
            u'<StackPanel Margin="20,16,20,20">'
            u'<TextBlock Text="Profile name" Foreground="' + fg + u'" FontSize="11" Margin="0,0,0,4" FontWeight="SemiBold"/>'
            u'<TextBox x:Name="TxtName" Background="' + input_bg + u'" Foreground="' + fg + u'"'
            u'  BorderBrush="' + border_color + u'" BorderThickness="1" Padding="8,5"'
            u'  FontSize="12" Margin="0,0,0,14"/>'
            u'<RadioButton x:Name="RbCopy" Content="Copy from current settings"'
            u'  Foreground="' + fg + u'" FontSize="12" Margin="0,0,0,6" IsChecked="True"/>'
            u'<RadioButton x:Name="RbDefault" Content="Use default settings"'
            u'  Foreground="' + fg + u'" FontSize="12" Margin="0,0,0,6"/>'
            u'<RadioButton x:Name="RbImport" Content="Import from a file"'
            u'  Foreground="' + fg + u'" FontSize="12" Margin="0,0,0,16"/>'
            u'<Button x:Name="BtnCreate" Content="Create"'
            u'  Background="' + btn_bg + u'" Foreground="White"'
            u'  BorderThickness="0" Padding="0,8" FontSize="13" FontWeight="SemiBold" Cursor="Hand"/>'
            u'</StackPanel>'
            u'</Window>'
        )

        try:
            from System.IO import StringReader
            from System.Xml import XmlReader
            from System.Windows.Markup import XamlReader as WpfXamlReader

            reader = XmlReader.Create(StringReader(xaml_str))
            self._win = WpfXamlReader.Load(reader)
            self._win.FindName("BtnCreate").Click += self._on_create
            self._win.ShowDialog()
        except Exception as ex:
            show_alert("Could not open Create Profile dialog: " + str(ex), is_error=True)

    def _on_create(self, sender, e):
        name = self._win.FindName("TxtName").Text.strip()
        if not name:
            return

        rb_copy   = self._win.FindName("RbCopy")
        rb_import = self._win.FindName("RbImport")

        if rb_import.IsChecked:
            from Microsoft.Win32 import OpenFileDialog
            dlg = OpenFileDialog()
            dlg.Filter = "Settings Files (*.json;*.xml)|*.json;*.xml|All Files (*.*)|*.*"
            if dlg.ShowDialog() != True:
                return
            import_path = dlg.FileName
            ext = os.path.splitext(import_path)[1].lower()
            rules = []
            try:
                if ext == ".json":
                    import codecs
                    with codecs.open(import_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    schemes = data.get("schemes", {})
                    if not schemes:
                        show_alert("No profiles found in the selected JSON file.", is_warning=True)
                        return
                    
                    if len(schemes) == 1:
                        rules = list(schemes.values())[0]
                    else:
                        # Let user pick which profile to import
                        scheme_names = sorted(schemes.keys())
                        chosen = forms.SelectFromList.show(
                            scheme_names,
                            title="Select Profile to Import",
                            multiselect=False
                        )
                        if not chosen:
                            return
                        rules = schemes[chosen]

                else:
                    from System.Xml import XmlDocument
                    xdoc = XmlDocument()
                    xdoc.Load(import_path)
                    
                    # Try our format first
                    rules_node = xdoc.SelectSingleNode("//NamingRules")
                    if rules_node:
                        for node in rules_node.SelectNodes("Rule"):
                            param_name = node.GetAttribute("ParameterName")
                            if param_name:
                                rules.append({
                                    "ParameterName": param_name,
                                    "Prefix": node.GetAttribute("Prefix") or "",
                                    "Suffix": node.GetAttribute("Suffix") or "",
                                    "Separator": node.GetAttribute("Separator") or ""
                                })
                    else:
                        # Try DiRoots ProSheets format
                        combine_params = xdoc.SelectNodes("//SelectSheetParameters/CombineParameters/ParameterModel")
                        for node in combine_params:
                            p_name = node.SelectSingleNode("ParameterName")
                            if not p_name or not p_name.InnerText: continue
                            
                            pref_node = node.SelectSingleNode("Prefix")
                            suff_node = node.SelectSingleNode("Suffix")
                            pref_val = pref_node.InnerText if pref_node else ""
                            suff_val = suff_node.InnerText if suff_node else ""
                            
                            sep_val = ""
                            if node.Attributes:
                                for attr in node.Attributes:
                                    if "preserve" in attr.Name.lower() or "space" in attr.Name.lower():
                                        sep_val = attr.Value
                                        break
                                        
                            rules.append({
                                "ParameterName": p_name.InnerText,
                                "Prefix": pref_val,
                                "Suffix": suff_val,
                                "Separator": sep_val
                            })
                            
            except Exception as ex:
                show_alert("Import error: " + str(ex), is_error=True)
                return
            self.result_rules = rules
            self.is_copy = False
        elif rb_copy.IsChecked:
            current_rules = self._settings.get("schemes", {}).get(self._current_scheme_name, [])
            self.result_rules = list(current_rules)
            self.is_copy = True
        else:
            self.result_rules = []
            self.is_copy = False

        self.result_name = name
        self._win.Close()


# ------------------------------------------------------------------------------
# Options Window
# ------------------------------------------------------------------------------
class OptionsWindow(forms.WPFWindow):

    def __init__(self, xaml_file_name, settings):
        forms.WPFWindow.__init__(self, xaml_file_name)
        self.settings = settings

        # Load values into UI
        opt = self.settings.get("export_options", {})
        theme = self.settings.get("theme", "Dark")

        if theme == "Light":
            self.RbThemeLight.IsChecked = True
        else:
            self.RbThemeDark.IsChecked = True

        self.RbTempHideOff.IsChecked = opt.get("temp_hide_off", True)
        self.RbTempHideLeave.IsChecked = not opt.get("temp_hide_off", True)

        self.RbWorksharingOff.IsChecked = opt.get("worksharing_off", True)
        self.RbWorksharingLeave.IsChecked = not opt.get("worksharing_off", True)

        self.RbRevealHiddenOff.IsChecked = opt.get("reveal_hidden_off", True)
        self.RbRevealHiddenLeave.IsChecked = not opt.get("reveal_hidden_off", True)

        self.RbRevealConstraintsOff.IsChecked = opt.get("reveal_constraints_off", True)
        self.RbRevealConstraintsLeave.IsChecked = not opt.get("reveal_constraints_off", True)

    def TitleBar_MouseDown(self, sender, e):
        try:
            self.DragMove()
        except:
            pass

    def MinimizeBtn_Click(self, sender, e):
        import System.Windows
        self.WindowState = System.Windows.WindowState.Minimized

    def MaximizeBtn_Click(self, sender, e):
        import System.Windows
        if self.WindowState == System.Windows.WindowState.Maximized:
            self.WindowState = System.Windows.WindowState.Normal
        else:
            self.WindowState = System.Windows.WindowState.Maximized

    def CloseBtn_Click(self, sender, e):
        self.Close()

    def BtnCancel_Click(self, sender, e):
        self.Close()

    def BtnSave_Click(self, sender, e):
        opt = self.settings.get("export_options", {})

        opt["temp_hide_off"] = self.RbTempHideOff.IsChecked
        opt["worksharing_off"] = self.RbWorksharingOff.IsChecked
        opt["reveal_hidden_off"] = self.RbRevealHiddenOff.IsChecked
        opt["reveal_constraints_off"] = self.RbRevealConstraintsOff.IsChecked

        self.settings["export_options"] = opt
        self.settings["theme"] = "Light" if self.RbThemeLight.IsChecked else "Dark"

        save_settings(self.settings)
        show_alert("Export options saved successfully!")
        self.Close()

# Export Manager Main Form (Wizard Controller)
# ------------------------------------------------------------------------------
from System.Windows import Window

class CustomConflictWindow(Window):
    def __init__(self, filename, ext, show_apply_all):
        self.result = "Skip"
        self.apply_all = False
        
        xaml_code = """<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="File Already Exists" Width="430" SizeToContent="Height" WindowStartupLocation="CenterScreen" ResizeMode="NoResize" ShowInTaskbar="False"  Background="#F5F5F5">
    <Grid Margin="15,15,15,20">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>
        
        <StackPanel Grid.Row="0" Orientation="Horizontal">
            <TextBlock Text="⚠️" FontSize="32" Margin="0,0,15,0" VerticalAlignment="Top" Foreground="#FFCC00"/>
            <TextBlock x:Name="TxtMessage" Text="" TextWrapping="Wrap" FontSize="13" VerticalAlignment="Top" Width="330" Margin="0,5,0,0"/>
        </StackPanel>
        
        <CheckBox x:Name="ChkApplyToAll" Grid.Row="1" Content="Do this for all remaining conflicts" FontSize="13" Margin="47,15,0,15" VerticalAlignment="Center" Foreground="#333333"/>
        
        <StackPanel Grid.Row="2" Orientation="Horizontal" HorizontalAlignment="Right">
            <Button x:Name="BtnReplace" Content="Replace" Width="70" Height="26" Margin="5,0" Background="#0078D7" Foreground="White" BorderThickness="0" Cursor="Hand"/>
            <Button x:Name="BtnRename" Content="Rename" Width="70" Height="26" Margin="5,0" Background="White" BorderBrush="#CCCCCC" Cursor="Hand"/>
            <Button x:Name="BtnSkip" Content="Skip" Width="70" Height="26" Margin="5,0,0,0" Background="White" BorderBrush="#CCCCCC" Cursor="Hand"/>
        </StackPanel>
    </Grid>
</Window>"""
        import wpf
        import System
        from System.IO import StringReader
        wpf.LoadComponent(self, StringReader(xaml_code))
        
        self.TxtMessage.Text = "A file named '{}{}' already exists in the destination.\n\nWhat would you like to do?".format(filename, ext)
        
        if not show_apply_all:
            self.ChkApplyToAll.Visibility = System.Windows.Visibility.Collapsed
            
        self.BtnReplace.Click += self.on_replace
        self.BtnRename.Click += self.on_rename
        self.BtnSkip.Click += self.on_skip
        
    def on_replace(self, sender, args):
        self.result = "Replace"
        self.apply_all = self.ChkApplyToAll.IsChecked
        self.Close()
        
    def on_rename(self, sender, args):
        self.result = "Rename"
        self.apply_all = self.ChkApplyToAll.IsChecked
        self.Close()
        
    def on_skip(self, sender, args):
        self.result = "Skip"
        self.apply_all = self.ChkApplyToAll.IsChecked
        self.Close()
        
    def show_dialog(self):
        self.ShowDialog()
        return self.result, self.apply_all
class ExportManagerForm(forms.WPFWindow):
    def __init__(self, xaml_file_name, sheets, views):
        forms.WPFWindow.__init__(self, xaml_file_name)

        try:
            import System
            from System.Windows.Media.Imaging import BitmapImage
            from System import Uri
            tab_dir = os.path.dirname(os.path.dirname(__commandpath__))
            logo_path = os.path.join(tab_dir, "About.panel", "About.pushbutton", "logo.png")
            if os.path.exists(logo_path):
                self.TitleLogo.Source = BitmapImage(Uri(logo_path))
        except Exception as e:
            pass

        # Load naming settings
        self.settings = load_settings()
        active = self.settings.get("active_scheme", "Default")
        self.active_scheme_parts = self.settings.get("schemes", {}).get(active, [])

        self.active_combined_scheme_parts = []
        if "combined_schemes" in self.settings:
            active_comb = self.settings.get("active_combined_scheme", "Default")
            if active_comb in self.settings["combined_schemes"]:
                self.active_combined_scheme_parts = self.settings["combined_schemes"][active_comb]
                        # Set default export folder (User Desktop)
        self.export_path = os.path.join(os.environ["USERPROFILE"], "Desktop")
        self.TxtExportPath.Text = self.export_path

        # Wrap sheets into ViewModels
        self.sheets = [SheetViewModel(s, self.active_scheme_parts, doc, is_view=False) for s in sheets]
        self.sheets.sort(key=lambda x: x.SheetNumber)

        # Wrap views into ViewModels
        self.views = [SheetViewModel(v, self.active_scheme_parts, doc, is_view=True) for v in views]
        self.views.sort(key=lambda x: x.SheetName)

        self.current_items = self.sheets
        self.GridSheets.ItemsSource = self.current_items

        # Populate Setups
        self.print_settings = list(DB.FilteredElementCollector(doc).OfClass(DB.PrintSetting).ToElements())
        self.dwg_settings = list(DB.FilteredElementCollector(doc).OfClass(DB.ExportDWGSettings).ToElements())

        self.pdf_setting_names = [ps.Name for ps in self.print_settings]
        self.dwg_setting_names = [ds.Name for ds in self.dwg_settings]

        self.pdf_setting_names.insert(0, "<In-Session / Default>")
        self.dwg_setting_names.insert(0, "<In-Session / Default>")

        self.CmbPdfSetup.ItemsSource = self.pdf_setting_names
        self.CmbDwgSetup.ItemsSource = self.dwg_setting_names

        if self.pdf_setting_names: self.CmbPdfSetup.SelectedIndex = 0
        if self.dwg_setting_names: self.CmbDwgSetup.SelectedIndex = 0

        # Initialize naming schemes
        self.reload_schemes()
        self.load_viewsets()
        self.update_combined_filename_preview()
        self.update_selection_stats()

        # Select first tab by default
        self.MainTabControl.SelectedIndex = 0

        # Load split by format setting
        split_by_format = self.settings.get("split_by_format", False)
        if split_by_format:
            self.RbSplitByFormat.IsChecked = True
        else:
            self.RbSaveSameFolder.IsChecked = True

        self.CmbPdfSetup.SelectionChanged += self.CmbPdfSetup_SelectionChanged
        self.CmbDwgSetup.SelectionChanged += self.CmbDwgSetup_SelectionChanged
        self._init_done = True

    def reload_schemes(self):
        settings = load_settings()
        active = settings.get("active_scheme", "Default")
        schemes_list = list(settings["schemes"].keys())
        
        if "Default" in schemes_list:
            schemes_list.remove("Default")
            schemes_list.sort(key=lambda s: s.lower())
            schemes_list.insert(0, "Default")
        else:
            schemes_list.sort(key=lambda s: s.lower())

        self.CmbProfile.ItemsSource = schemes_list
        if active in schemes_list:
            self.CmbProfile.SelectedItem = active
        elif schemes_list:
            self.CmbProfile.SelectedIndex = 0

        self.active_scheme_parts = settings["schemes"].get(self.CmbProfile.SelectedItem, [])

    # ViewSheetSets logic
    def load_viewsets(self):
        settings = load_settings()
        self.viewsets_dict = settings.get("view_sets", {})

        self.viewset_names = list(self.viewsets_dict.keys())
        self.viewset_names.sort()

        # Load Revit built-in ViewSheetSets (print sets)
        self.revit_viewsets = {}
        try:
            revit_sets = DB.FilteredElementCollector(doc).OfClass(DB.ViewSheetSet).ToElements()
            for vs in revit_sets:
                sheet_nums = []
                for view in vs.Views:
                    if hasattr(view, 'SheetNumber'):
                        sheet_nums.append(view.SheetNumber)
                    else:
                        sheet_nums.append(view.Name)
                self.revit_viewsets[vs.Name] = sheet_nums
        except:
            pass

        revit_set_names = sorted(self.revit_viewsets.keys())

        # Populate the Filter dropdown: label, then Revit print sets only
        filter_items = ["-- Filter by V/S Set --"] + revit_set_names

        self.CmbFilterSets.ItemsSource = filter_items
        self.CmbFilterSets.SelectedIndex = 0

        # Lookup: name -> sheet number list
        self.all_viewsets_dict = dict(self.revit_viewsets)



    def RbMode_Checked(self, sender, e):
        """Switch the DataGrid between Sheets and Views."""
        if not hasattr(self, "sheets") or not hasattr(self, "views"):
            return
        if self.RbViews.IsChecked:
            self.current_items = self.views
        else:
            self.current_items = self.sheets
        self.GridSheets.ItemsSource = None
        self.GridSheets.ItemsSource = self.current_items
        self.update_selection_stats()

    def CmbFilterSets_SelectionChanged(self, sender, e):
        """Filter/select items in the grid based on the chosen saved set."""
        # Guard: event can fire during XAML loading before __init__ completes
        if not hasattr(self, "current_items") or not hasattr(self, "all_viewsets_dict"):
            return

        selected = self.CmbFilterSets.SelectedItem
        # Ignore label/separator rows
        if not selected or selected.startswith("--") or selected.startswith("---"):
            for sv in self.current_items:
                sv.IsSelected = False
            if hasattr(self, 'CbShowActive'):
                self.CbShowActive.IsChecked = False
            self.filter_sheets()
            self.update_selection_stats()
            return

        set_numbers = self.all_viewsets_dict.get(selected, [])

        for sv in self.current_items:
            sv.IsSelected = (sv.SheetNumber in set_numbers)

        if hasattr(self, 'CbShowActive'):
            self.CbShowActive.IsChecked = True
            
        self.filter_sheets()
        self.update_selection_stats()

    def CmbSetActions_SelectionChanged(self, sender, e):
        """Handle action ComboBox: New set / Add to Existing / Delete set."""
        # Guard: this event can fire during XAML loading before __init__ completes
        if not hasattr(self, "CmbSetActions") or not hasattr(self, "current_items"):
            return
        cmb = self.CmbSetActions
        item = cmb.SelectedItem
        if item is None:
            return
        try:
            label = item.Content if hasattr(item, "Content") else str(item)
        except:
            label = str(item)

        if label == "Unsaved Set":
            return

        # Reset back to "Unsaved Set" after action resolves
        try:
            if label == "New set":
                self._action_new_set()
            elif label == "Add to Existing":
                self._action_add_to_existing()
            elif label == "Delete set":
                self._action_delete_set()
        finally:
            cmb.SelectedIndex = 0

    def _action_new_set(self):
        """Save currently selected items as a new named set."""
        selected_vms = [sv for sv in self.current_items if sv.IsSelected]
        if not selected_vms:
            show_alert("No items selected to save.", is_warning=True)
            return

        set_name = show_text_input("New View/Sheet Set", "Enter a name for the new set:")
        if not set_name:
            return

        try:
            settings = load_settings()
            if "view_sets" not in settings:
                settings["view_sets"] = {}

            sheet_numbers = [sv.SheetNumber for sv in selected_vms]
            settings["view_sets"][set_name] = sheet_numbers
            save_settings(settings)
            show_alert("Set '{}' saved successfully.".format(set_name))
            self.load_viewsets()

            # Select the new set in the filter dropdown
            try:
                self.CmbFilterSets.SelectedIndex = self.viewset_names.index(set_name) + 1
            except ValueError:
                pass
        except Exception as ex:
            show_alert("Failed to save set:\n" + str(ex), is_error=True)

    def _action_add_to_existing(self):
        """Add currently selected items to an already saved set."""
        if not self.viewset_names:
            show_alert("No saved sets found. Create a 'New set' first.", is_warning=True)
            return

        selected_vms = [sv for sv in self.current_items if sv.IsSelected]
        if not selected_vms:
            show_alert("No items selected to add.", is_warning=True)
            return

        # Ask user which set to add to via a simple text input with hint
        hint = "Saved sets: " + ", ".join(self.viewset_names)
        set_name = show_text_input("Add to Existing Set", "Enter the set name to add to:\n({})".format(hint))
        if not set_name:
            return
        if set_name not in self.viewsets_dict:
            show_alert("Set '{}' not found.".format(set_name), is_warning=True)
            return

        try:
            settings = load_settings()
            existing = settings["view_sets"].get(set_name, [])
            new_numbers = [sv.SheetNumber for sv in selected_vms]
            merged = list(set(existing + new_numbers))
            settings["view_sets"][set_name] = merged
            save_settings(settings)
            show_alert("Added {} item(s) to set '{}'.".format(len(new_numbers), set_name))
            self.load_viewsets()
        except Exception as ex:
            show_alert("Failed to update set:\n" + str(ex), is_error=True)

    def _action_delete_set(self):
        """Delete the set currently selected in the Filter dropdown."""
        idx = self.CmbFilterSets.SelectedIndex
        if idx <= 0:
            show_alert("Select a set in the 'Filter by V/S Set' dropdown first.", is_warning=True)
            return

        set_name = self.viewset_names[idx - 1]

        try:
            settings = load_settings()
            if "view_sets" in settings and set_name in settings["view_sets"]:
                del settings["view_sets"][set_name]
                save_settings(settings)
            show_alert("Set '{}' deleted.".format(set_name))
            self.load_viewsets()
            self.CmbFilterSets.SelectedIndex = 0
        except Exception as ex:
            show_alert("Failed to delete set:\n" + str(ex), is_error=True)

    def TitleBar_MouseDown(self, sender, e):
        try:
            self.DragMove()
        except:
            pass
    def SortBtn_Click(self, sender, e):
        try:
            e.Handled = True
            prop_name = sender.Tag
            if not prop_name:
                return

            if not hasattr(self, "sort_dirs"):
                self.sort_dirs = {}

            current_dir = self.sort_dirs.get(prop_name, "Descending")
            if current_dir == "Ascending":
                new_dir = "Descending"
                sender.Content = u"\u25BC" # ▼
            else:
                new_dir = "Ascending"
                sender.Content = u"\u25B2" # ▲

            self.sort_dirs[prop_name] = new_dir
            reverse = (new_dir == "Descending")

            items = getattr(self, "current_items", self.sheets)

            items.sort(key=lambda x: str(getattr(x, prop_name, "")), reverse=reverse)

            # Re-assign ItemsSource to force UI update, since view.Refresh() doesn't work for Python list order changes
            new_list = [x for x in items]
            selected = list(self.GridSheets.SelectedItems)
            self.GridSheets.ItemsSource = None
            self.GridSheets.ItemsSource = new_list
            for item in selected:
                self.GridSheets.SelectedItems.Add(item)

            if hasattr(self, "current_items"):
                self.current_items = new_list
            else:
                self.sheets = new_list

        except Exception as ex:
            show_alert("Sort error: " + str(ex), is_error=True)

    def MinimizeBtn_Click(self, sender, e):
        import System.Windows
        self.WindowState = System.Windows.WindowState.Minimized

    def MaximizeBtn_Click(self, sender, e):
        import System.Windows
        if self.WindowState == System.Windows.WindowState.Maximized:
            self.WindowState = System.Windows.WindowState.Normal
        else:
            self.WindowState = System.Windows.WindowState.Maximized

    def CloseBtn_Click(self, sender, e):
        self.DialogResult = False
        self.Close()

    # Tab 1: Selection Logic
    def update_selection_stats(self):
        items = getattr(self, "current_items", self.sheets)
        selected_count = sum(1 for sv in items if sv.IsSelected)
        total_count = len(items)
        label = "views" if getattr(self, "RbViews", None) and self.RbViews.IsChecked else "sheets"
        self.StatusTextBlock.Text = "{} {} selected. Total: {}".format(selected_count, label, total_count)

    def filter_sheets(self):
        search_text = self.TxtSearch.Text.lower().strip()
        items = getattr(self, "current_items", self.sheets)
        filtered = []
        
        show_active_only = False
        if hasattr(self, 'CbShowActive') and self.CbShowActive.IsChecked:
            show_active_only = True
            
        for sv in items:
            match_search = not search_text or (search_text in sv.SheetNumber.lower() or search_text in sv.SheetName.lower())
            match_active = (not show_active_only) or sv.IsSelected
            if match_search and match_active:
                filtered.append(sv)
                
        self.GridSheets.ItemsSource = filtered

    def CbShowActive_Click(self, sender, e):
        self.filter_sheets()

    def TxtSearch_TextChanged(self, sender, e):
        self.filter_sheets()

    def CbHeaderSelectAll_Click(self, sender, e):
        is_checked = sender.IsChecked
        items = self.GridSheets.ItemsSource or self.sheets
        for sv in items:
            sv.IsSelected = is_checked
        self.GridSheets.Items.Refresh()
        self.update_selection_stats()

    def CbSheetSelect_Click(self, sender, e):
        self.update_selection_stats()

    # Tab 2: Format Logic
    def CbFormat_Click(self, sender, e):
        if hasattr(self, "CbPDF") and hasattr(self, "CbDWG"):
            self._save_profile_setting("is_pdf_checked", self.CbPDF.IsChecked == True)
            self._save_profile_setting("is_dwg_checked", self.CbDWG.IsChecked == True)

    def update_combined_filename_preview(self):
        try:
            name_parts = []
            for part in self.active_combined_scheme_parts:
                sample_val = get_sample_value(doc, part.get("ParameterName", ""), None)
                name_parts.append(part.get("Prefix", "") + sample_val + part.get("Suffix", "") + part.get("Separator", ""))

            final_name = "".join(name_parts)
            if hasattr(self, 'TxtCombinedFileName'):
                self.TxtCombinedFileName.Text = final_name if final_name else "Combined_PDF"
        except:
            pass

    def RbFileOption_Click(self, sender, e):
        enabled = (self.RbCombineFiles.IsChecked == True)
        self.PanelCombineOptions.IsEnabled = enabled
        self._save_profile_setting("is_combined", enabled)
        
        if hasattr(self, "RbSaveSameFolder") and hasattr(self, "RbSplitByFormat"):
            self.RbSaveSameFolder.IsChecked = enabled
            self.RbSplitByFormat.IsChecked = not enabled

    def BtnCombinedNaming_Click(self, sender, e):
        active = self.CmbProfile.SelectedItem or "Default"
        theme = self.settings.get("theme", "Dark")
        b_name = "NamingBuilder_Light.xaml" if theme == "Light" else "NamingBuilder.xaml"
        builder_xaml_path = os.path.join(os.path.dirname(__file__), b_name)

        sample_elements = [s.Sheet for s in self.sheets] if self.sheets else []
        builder_form = NamingBuilderForm(builder_xaml_path, active, doc, sample_elements, is_combined=True)
        if builder_form.ShowDialog():
            self.settings = load_settings()
            if "combined_schemes" in self.settings and active in self.settings["combined_schemes"]:
                self.active_combined_scheme_parts = self.settings["combined_schemes"][active]
            self.update_combined_filename_preview()
    def BtnCombineBrowse_Click(self, sender, e):
        from System.Windows.Forms import FolderBrowserDialog, DialogResult
        dlg = FolderBrowserDialog()
        dlg.Description = "Select folder to save combined PDF"
        if dlg.ShowDialog() == DialogResult.OK:
            self.TxtCombineFolder.Text = dlg.SelectedPath

    def CmbProfile_SelectionChanged(self, sender, e):
        active = self.CmbProfile.SelectedItem
        if active:
            settings = load_settings()
            settings["active_scheme"] = active
            save_settings(settings)
            self.active_scheme_parts = settings["schemes"].get(active, [])

            # Recalculate naming previews for all sheets and views
            for sv in self.sheets:
                sv.update_filename(self.active_scheme_parts, doc)
            for sv in self.views:
                sv.update_filename(self.active_scheme_parts, doc)
            self.GridSheets.Items.Refresh()
            
            # Load profile specific combined setups
            self.active_combined_scheme_parts = settings.get("combined_schemes", {}).get(active, [])
            self.update_combined_filename_preview()
            
            # Load profile specific format setups
            if "profile_settings" in settings and hasattr(self, 'CmbPdfSetup') and hasattr(self, 'CmbDwgSetup'):
                p_settings = settings["profile_settings"].get(active, {})
                if "pdf_setting" in p_settings and p_settings["pdf_setting"] in getattr(self, 'pdf_setting_names', []):
                    self.CmbPdfSetup.SelectedItem = p_settings["pdf_setting"]
                if "dwg_setting" in p_settings and p_settings["dwg_setting"] in getattr(self, 'dwg_setting_names', []):
                    self.CmbDwgSetup.SelectedItem = p_settings["dwg_setting"]
                if hasattr(self, "CbPDF"):
                    self.CbPDF.IsChecked = p_settings.get("is_pdf_checked", True)
                if hasattr(self, "CbDWG"):
                    self.CbDWG.IsChecked = p_settings.get("is_dwg_checked", True)
                if hasattr(self, "RbCombineFiles"):
                    is_comb = p_settings.get("is_combined", "combined" in active.lower())
                    self.RbCombineFiles.IsChecked = is_comb
                    self.RbSeparateFiles.IsChecked = not is_comb
                    self.PanelCombineOptions.IsEnabled = is_comb
                    
                    if hasattr(self, "RbSaveSameFolder") and hasattr(self, "RbSplitByFormat"):
                        self.RbSaveSameFolder.IsChecked = is_comb
                        self.RbSplitByFormat.IsChecked = not is_comb

    def _save_profile_setting(self, key, value):
        if not hasattr(self, "CmbProfile"): return
        active = self.CmbProfile.SelectedItem
        if not active or value is None: return
        settings = load_settings()
        if "profile_settings" not in settings:
            settings["profile_settings"] = {}
        if active not in settings["profile_settings"]:
            settings["profile_settings"][active] = {}
        settings["profile_settings"][active][key] = value
        save_settings(settings)

    def CmbPdfSetup_SelectionChanged(self, sender, e):
        if getattr(self, '_init_done', False):
            self._save_profile_setting("pdf_setting", self.CmbPdfSetup.SelectedItem)

    def CmbDwgSetup_SelectionChanged(self, sender, e):
        if getattr(self, '_init_done', False):
            self._save_profile_setting("dwg_setting", self.CmbDwgSetup.SelectedItem)

    def BtnAddProfile_Click(self, sender, e):
        settings = load_settings()
        current = self.CmbProfile.SelectedItem or "Default"

        dialog = CreateProfileDialog(current, settings)

        if not dialog.result_name:
            return

        new_name = dialog.result_name
        if new_name in settings["schemes"]:
            show_alert("A profile named '{}' already exists.".format(new_name), is_warning=True)
            return

        settings["schemes"][new_name] = dialog.result_rules or []
        settings["active_scheme"] = new_name
        
        # Duplicate profile settings if copied
        if getattr(dialog, 'is_copy', False):
            if "profile_settings" in settings and current in settings["profile_settings"]:
                if "profile_settings" not in settings:
                    settings["profile_settings"] = {}
                settings["profile_settings"][new_name] = dict(settings["profile_settings"][current])
                
        save_settings(settings)
        self.reload_schemes()
        # Refresh filename previews if rules were copied
        self.CmbProfile_SelectionChanged(None, None)


    def BtnDeleteProfile_Click(self, sender, e):
        active = self.CmbProfile.SelectedItem
        if not active or active == "Default":
            show_alert("Cannot delete Default profile.", is_warning=True)
            return

        settings = load_settings()
        if active in settings["schemes"]:
            del settings["schemes"][active]
            settings["active_scheme"] = "Default"
            save_settings(settings)
            self.reload_schemes()

    def BtnRenameProfile_Click(self, sender, e):
        active = self.CmbProfile.SelectedItem
        if not active:
            show_alert("No profile selected.", is_warning=True)
            return

        new_name = show_text_input("Rename Profile", "Enter new name for '{}'".format(active), default_value=active)
        if not new_name or new_name == active:
            return

        settings = load_settings()
        if new_name in settings["schemes"]:
            show_alert("A profile named '{}' already exists.".format(new_name), is_warning=True)
            return

        # Copy scheme data under new name, delete old
        settings["schemes"][new_name] = settings["schemes"].pop(active)
        settings["active_scheme"] = new_name
        save_settings(settings)
        self.reload_schemes()


    def BtnNamingBuilder_Click(self, sender, e):
        active = self.CmbProfile.SelectedItem or "Default"
        theme = load_settings().get("theme", "Dark")
        b_name = "NamingBuilder_Light.xaml" if theme == "Light" else "NamingBuilder.xaml"
        builder_xaml_path = os.path.join(os.path.dirname(__file__), b_name)
        raw_sheets = [sv.Sheet for sv in self.sheets]

        builder_form = NamingBuilderForm(builder_xaml_path, active, doc, raw_sheets)
        if builder_form.ShowDialog():
            self.reload_schemes()
            # Recalculate naming previews
            for sv in self.sheets:
                sv.update_filename(self.active_scheme_parts, doc)
            self.GridSheets.Items.Refresh()

    def BtnSaveProfile_Click(self, sender, e):
        dialog = CustomProfileSaveWindow()
        res = dialog.ShowDialog()

        if res == "SaveAs":
            try:
                # Show SaveFileDialog
                from Microsoft.Win32 import SaveFileDialog
                dlg = SaveFileDialog()
                dlg.Filter = "XML Files (*.xml)|*.xml|All Files (*.*)|*.*"
                dlg.DefaultExt = ".xml"
                dlg.FileName = (self.CmbProfile.SelectedItem or "Default") + ".xml"

                if dlg.ShowDialog() == True:
                    save_path = dlg.FileName
                    active = self.CmbProfile.SelectedItem or "Default"
                    settings = load_settings()
                    scheme = settings["schemes"].get(active, [])

                    # Build simple XML manually to avoid IronPython xml module issues
                    xml_string = '<?xml version="1.0" encoding="utf-8"?>\n<Profile>\n'
                    xml_string += '  <Name>{}</Name>\n'.format(active)
                    xml_string += '  <NamingRules>\n'
                    for part in scheme:
                        param_name = part.get("ParameterName", "")
                        prefix = part.get("Prefix", "")
                        suffix = part.get("Suffix", "")
                        separator = part.get("Separator", "")

                        def xml_escape(val):
                            if not val:
                                return ""
                            # Ensure it is converted to string safely
                            if isinstance(val, unicode):
                                val = val.encode("utf-8")
                            val_str = str(val)
                            return val_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')

                        xml_string += '    <Rule ParameterName="{}" Prefix="{}" Suffix="{}" Separator="{}" />\n'.format(
                            xml_escape(param_name),
                            xml_escape(prefix),
                            xml_escape(suffix),
                            xml_escape(separator)
                        )
                    xml_string += '  </NamingRules>\n</Profile>'

                    import codecs
                    with codecs.open(save_path, "w", encoding="utf-8") as f:
                        u_xml = xml_string
                        if isinstance(u_xml, str):
                            u_xml = u_xml.decode("utf-8", "ignore")
                        f.write(u_xml)

                    show_alert("Profile successfully exported to XML!")
            except Exception as ex:
                show_alert("Error saving XML: " + str(ex), is_error=True)

        elif res == "Save":
            # Saving internally is actually automatic when editing, but we can show a confirmation
            show_alert("Profile saved successfully.")

    def BtnImportProfile_Click(self, sender, e):
        try:
            from Microsoft.Win32 import OpenFileDialog
            dlg = OpenFileDialog()
            dlg.Filter = "Settings Files (*.json;*.xml)|*.json;*.xml|JSON Settings (*.json)|*.json|XML Profile (*.xml)|*.xml|All Files (*.*)|*.*"
            dlg.DefaultExt = ".json"

            if dlg.ShowDialog() == True:
                import_path = dlg.FileName
                ext = os.path.splitext(import_path)[1].lower()

                imported_schemes = {}

                if ext == ".json":
                    # Import from our own naming_settings.json format
                    import codecs
                    with codecs.open(import_path, "r", encoding="utf-8") as f:
                        imported_data = json.load(f)

                    if "schemes" not in imported_data:
                        show_alert("Invalid settings JSON: No 'schemes' key found.", is_error=True)
                        return

                    imported_schemes = imported_data["schemes"]
                    if not imported_schemes:
                        show_alert("No profiles found in the JSON file.", is_error=True)
                        return

                else:
                    # Import from XML format
                    from System.Xml import XmlDocument
                    xdoc = XmlDocument()
                    xdoc.Load(import_path)

                    name_node = xdoc.SelectSingleNode("//Name")
                    if not name_node:
                        show_alert("Invalid profile XML: Missing Name element.", is_error=True)
                        return
                    profile_name = name_node.InnerText.strip()
                    if not profile_name:
                        show_alert("Invalid profile XML: Profile Name is empty.", is_error=True)
                        return

                    rules_node = xdoc.SelectSingleNode("//NamingRules")
                    imported_rules = []
                    if rules_node:
                        rule_nodes = rules_node.SelectNodes("Rule")
                        for node in rule_nodes:
                            param_name = node.GetAttribute("ParameterName") or node.GetAttribute("Value")
                            prefix = node.GetAttribute("Prefix")
                            suffix = node.GetAttribute("Suffix")
                            separator = node.GetAttribute("Separator")
                            if param_name:
                                imported_rules.append({
                                    "ParameterName": param_name,
                                    "Prefix": prefix or "",
                                    "Suffix": suffix or "",
                                    "Separator": separator or ""
                                })
                    else:
                        # Try DiRoots ProSheets format
                        combine_params = xdoc.SelectNodes("//SelectSheetParameters/CombineParameters/ParameterModel")
                        for node in combine_params:
                            p_name = node.SelectSingleNode("ParameterName")
                            if not p_name or not p_name.InnerText: continue
                            
                            pref_node = node.SelectSingleNode("Prefix")
                            suff_node = node.SelectSingleNode("Suffix")
                            pref_val = pref_node.InnerText if pref_node else ""
                            suff_val = suff_node.InnerText if suff_node else ""
                            
                            sep_val = ""
                            if node.Attributes:
                                for attr in node.Attributes:
                                    if "preserve" in attr.Name.lower() or "space" in attr.Name.lower():
                                        sep_val = attr.Value
                                        break
                                        
                            imported_rules.append({
                                "ParameterName": p_name.InnerText,
                                "Prefix": pref_val,
                                "Suffix": suff_val,
                                "Separator": sep_val
                            })

                    if not imported_rules:
                        show_alert("No valid naming rules found in the XML file.", is_error=True)
                        return

                    imported_schemes = {profile_name: imported_rules}

                # Merge imported schemes into current settings
                settings = load_settings()
                last_imported = None

                for profile_name, rules in imported_schemes.items():
                    if profile_name in settings["schemes"]:
                        base_name = profile_name
                        counter = 1
                        while "{}_{}" .format(base_name, counter) in settings["schemes"]:
                            counter += 1
                        profile_name = "{}_{}".format(base_name, counter)

                    settings["schemes"][profile_name] = rules
                    last_imported = profile_name

                if last_imported:
                    settings["active_scheme"] = last_imported
                    save_settings(settings)
                    self.reload_schemes()
                    self.CmbProfile_SelectionChanged(None, None)
                    show_alert("Imported {} profile(s) successfully!".format(len(imported_schemes)))

        except Exception as ex:
            show_alert("Error importing: " + str(ex), is_error=True)


    # Tab 3: Create Logic
    def BtnBrowse_Click(self, sender, e):
        selected_folder = forms.pick_folder(title="Select Export Destination")
        if selected_folder:
            self.export_path = selected_folder
            self.TxtExportPath.Text = self.export_path

    def generate_queue(self):
        selected_vms = [sv for sv in self.sheets if sv.IsSelected]
        queue = []

        export_pdf = self.CbPDF.IsChecked
        export_dwg = self.CbDWG.IsChecked

        for sv in selected_vms:
            if export_pdf:
                queue.append(QueueItemViewModel(sv, "PDF", self.active_scheme_parts, doc))
            if export_dwg:
                queue.append(QueueItemViewModel(sv, "DWG", self.active_scheme_parts, doc))

        self.queue_items = queue
        self.GridQueue.ItemsSource = self.queue_items

    # Wizard Navigation
    def MainTabControl_SelectionChanged(self, sender, e):
        if not hasattr(self, 'BtnBack') or not hasattr(self, 'BtnNext'):
            return
        idx = self.MainTabControl.SelectedIndex
        if idx == 0:
            self.BtnBack.IsEnabled = False
            self.BtnNext.Content = "Next"
        elif idx == 1:
            self.BtnBack.IsEnabled = True
            self.BtnNext.Content = "Next"
        elif idx == 2:
            self.BtnBack.IsEnabled = True
            self.BtnNext.Content = "Create"
            self.generate_queue()

    def BtnBack_Click(self, sender, e):
        idx = self.MainTabControl.SelectedIndex
        if idx > 0:
            self.MainTabControl.SelectedIndex = idx - 1

    def BtnNext_Click(self, sender, e):
        if getattr(self, "_exporting", False):
            self._cancel_export = True
            self.BtnNext.Content = "Cancelling..."
            return

        idx = self.MainTabControl.SelectedIndex
        if idx == 0:
            # Check selection
            selected_count = sum(1 for sv in self.sheets if sv.IsSelected)
            if selected_count == 0:
                show_alert("Please select at least one sheet before proceeding.", is_warning=True)
                return
            self.MainTabControl.SelectedIndex = 1
        elif idx == 1:
            # Check format
            if not self.CbPDF.IsChecked and not self.CbDWG.IsChecked:
                show_alert("Please select at least one export format.", is_warning=True)
                return
            self.MainTabControl.SelectedIndex = 2
        elif idx == 2:
            # Trigger Export Execution
            self.run_export()

    def BtnResetSettings_Click(self, sender, e):
        theme = load_settings().get("theme", "Dark")
        opt_name = "OptionsUI_Light.xaml" if theme == "Light" else "OptionsUI.xaml"
        xaml_path = os.path.join(os.path.dirname(__file__), opt_name)
        settings = load_settings()
        opt_window = OptionsWindow(xaml_path, settings)
        opt_window.ShowDialog()

    # UI yielding events
    def do_events(self):
        from System.Windows.Threading import DispatcherFrame, Dispatcher
        from System import Action

        frame = DispatcherFrame()
        def exit_frame(f):
            f.Continue = False

        Dispatcher.CurrentDispatcher.BeginInvoke(
            System.Windows.Threading.DispatcherPriority.Background,
            Action[DispatcherFrame](exit_frame),
            frame
        )
        Dispatcher.PushFrame(frame)

    def check_and_resolve_filename(self, folder, filename, ext, show_apply_all=True):
        import os
        full_path = os.path.join(folder, filename + ext)
        if not os.path.exists(full_path):
            return filename
            
        locked = False
        try:
            if os.path.exists(full_path):
                # Try opening with read/write access. This will fail if the file is open/locked.
                # Safe for network drives (unlike rename).
                with open(full_path, 'r+'):
                    pass
        except (IOError, OSError):
            locked = True
            
        # Check 'apply to all' flags first (only for unlocked files)
        if not locked:
            if getattr(self, "replace_all", False):
                return filename
            if getattr(self, "skip_all", False):
                return None
            
        from pyrevit import forms
        
        if locked:
            res = forms.alert(
                "The file '{}{}' is currently OPEN in another program.\n\nPlease close the file before replacing it, or choose to Rename the new file.".format(filename, ext),
                title="File is Open",
                options=["Try Again", "Rename", "Skip"]
            )
            if res == "Try Again":
                return self.check_and_resolve_filename(folder, filename, ext, show_apply_all)
        else:
            try:
                conflict_window = CustomConflictWindow(filename, ext, show_apply_all)
                res, apply_all = conflict_window.show_dialog()
            except Exception as e:
                import traceback
                forms.alert("Error in CustomConflictWindow:\n" + str(e) + "\n\n" + traceback.format_exc())
                return None
            
            if apply_all:
                if res == "Replace":
                    self.replace_all = True
                elif res == "Skip":
                    self.skip_all = True
            
        
        if res == "Replace" and not locked:
            return filename
        elif res == "Replace All" and not locked:
            self.replace_all = True
            return filename
        elif res == "Skip All":
            self.skip_all = True
            return None
        elif res == "Rename":
            new_name = forms.ask_for_string(
                default=filename,
                prompt="Enter a new file name (without extension):",
                title="Rename File"
            )
            
            if new_name:
                return self.check_and_resolve_filename(folder, new_name, ext, show_apply_all)
            else:
                return None
        else:
            return None

    # Export Process
    def run_export(self):
        folder = self.TxtExportPath.Text.strip()
        import System
        if not folder or not System.IO.Directory.Exists(folder):
            show_alert("Please select a valid export directory.", is_warning=True)
            return

        if not self.queue_items:
            show_alert("Export queue is empty. Please select sheets and formats.", is_warning=True)
            return

        # Reset queue item status and target names for fresh export run
        self.replace_all = False
        self.skip_all = False
        for item in self.queue_items:
            item.Status = "Pending"
            item.TargetFileName = generate_filename(item.SheetVM.Sheet, self.active_scheme_parts, doc)
        
        self.GridQueue.Items.Refresh()
        self.ExportProgressBar.Value = 0
        self.TxtPercent.Text = "Completed 0%"
        self.do_events()

        pdf_idx = self.CmbPdfSetup.SelectedIndex
        selected_pdf_setting = self.print_settings[pdf_idx - 1] if pdf_idx > 0 else None
        
        pdf_zoom_type = None
        pdf_zoom_pct = None
        if selected_pdf_setting:
            from pyrevit import revit
            from Autodesk.Revit.UI.Events import TaskDialogShowingEventArgs
            def dismiss_dialog(sender, args):
                if args.GetType() == TaskDialogShowingEventArgs:
                    args.OverrideResult(1) # OK
            try:
                revit.uidoc.Application.DialogBoxShowing += dismiss_dialog
                ps = selected_pdf_setting.PrintParameters
                pdf_zoom_type = ps.ZoomType
                pdf_zoom_pct = ps.Zoom
            except:
                pass
            finally:
                revit.uidoc.Application.DialogBoxShowing -= dismiss_dialog

        dwg_idx = self.CmbDwgSetup.SelectedIndex
        selected_dwg_setting = self.dwg_settings[dwg_idx - 1] if dwg_idx > 0 else None

        # Disable navigation controls
        self.BtnBack.IsEnabled = False
        self.CloseBtn.IsEnabled = False
        
        # Setup Cancel button and lock Topmost
        self.BtnNext.IsEnabled = True
        self.BtnNext.Content = "Cancel"
        self._exporting = True
        self._cancel_export = False

        try:
            revit_version = int(float(__revit__.Application.VersionNumber))
        except:
            revit_version = 2022
        total = len(self.queue_items)

        # Save split_by_format setting
        try:
            settings = load_settings()
            settings["split_by_format"] = self.RbSplitByFormat.IsChecked
            save_settings(settings)
        except Exception:
            pass

        try:
            # --- PRE-FLIGHT CHECKS ---
            combine_pdf = hasattr(self, 'RbCombineFiles') and (self.RbCombineFiles.IsChecked == True)
            
            # 1. Combined PDF Pre-flight
            resolved_combined = None
            if combine_pdf:
                pdf_items = [item for item in self.queue_items if item.Format == "PDF"]
                if pdf_items:
                    combined_filename = self.TxtCombinedFileName.Text.strip() if hasattr(self, 'TxtCombinedFileName') else "Combined_PDF"
                    if not combined_filename:
                        combined_filename = "Combined_PDF"
                        
                    combine_folder = folder
                    if self.RbSplitByFormat.IsChecked:
                        combine_folder = os.path.join(folder, "PDF")
                        if not os.path.exists(combine_folder):
                            try:
                                os.makedirs(combine_folder)
                            except:
                                pass
                    
                    resolved_combined = self.check_and_resolve_filename(combine_folder, combined_filename, ".pdf", show_apply_all=False)
                    if not resolved_combined:
                        for item in pdf_items:
                            item.Status = "Skipped"

            # 2. Individual Files Pre-flight
            for item in self.queue_items:
                if item.Status == "Skipped":
                    continue
                    
                if item.Format == "PDF" and combine_pdf:
                    continue # Handled by combined
                    
                target_folder = folder
                if self.RbSplitByFormat.IsChecked:
                    target_folder = os.path.join(folder, item.Format)
                    if not os.path.exists(target_folder):
                        try:
                            os.makedirs(target_folder)
                        except:
                            pass
                            
                ext = ".pdf" if item.Format == "PDF" else ".dwg"
                resolved_name = self.check_and_resolve_filename(target_folder, item.TargetFileName, ext, show_apply_all=(total > 1))
                if resolved_name:
                    item.TargetFileName = resolved_name
                else:
                    item.Status = "Skipped"
                    
            self.GridQueue.Items.Refresh()
            self.do_events()

            # --- NORMAL EXPORT LOOP ---
            for idx, item in enumerate(self.queue_items):
                if self._cancel_export:
                    show_alert("Export cancelled by user.", is_warning=True)
                    break
                    
                if item.Status == "Skipped":
                    continue
                    
                item.Status = "Exporting..."
                self.GridQueue.Items.Refresh()
                self.do_events()

                success = False
                err_msg = ""

                target_folder = folder
                if self.RbSplitByFormat.IsChecked:
                    target_folder = os.path.join(folder, item.Format)

                try:
                    if item.Format == "PDF":
                        if combine_pdf:
                            success = True
                        elif revit_version >= 2022:
                            success = export_pdf_2022(target_folder, item.SheetVM.Sheet, item.TargetFileName, pdf_zoom_type, pdf_zoom_pct)
                        else:
                            success = False
                            err_msg = "PDF requires Revit 2022+"
                    elif item.Format == "DWG":
                        export_dwg(target_folder, item.SheetVM.Sheet, item.TargetFileName, selected_dwg_setting)
                        success = True
                except Exception as ex:
                    import traceback
                    success = False
                    err_msg = traceback.format_exc()

                if success:
                    item.Status = "Done"
                else:
                    item.Status = "Error"

                percent = int(((idx + 1) / float(total)) * 100)
                self.ExportProgressBar.Value = percent
                self.TxtPercent.Text = "Completed {}%".format(percent)
                self.GridQueue.Items.Refresh()
                self.do_events()

            # --- COMBINED PDF EXPORT ---
            if combine_pdf and not self._cancel_export and resolved_combined:
                pdf_items = [item for item in self.queue_items if item.Format == "PDF" and item.Status == "Done"]
                if pdf_items:
                    combine_folder = folder
                    if self.RbSplitByFormat.IsChecked:
                        combine_folder = os.path.join(folder, "PDF")
                        
                    sheets = [item.SheetVM.Sheet for item in pdf_items]
                    if revit_version >= 2022:
                        ok = export_combined_pdf_2022(combine_folder, sheets, resolved_combined, pdf_zoom_type, pdf_zoom_pct)
                        if not ok:
                            for item in pdf_items:
                                item.Status = "Error"
                    else:
                        show_alert("Combined PDF requires Revit 2022+", is_error=True)
                        for item in pdf_items:
                            item.Status = "Error"

            # --- EXCEL TRANSMITTAL EXPORT ---
            if getattr(self, 'CbExcelTransmittal', None) and self.CbExcelTransmittal.IsChecked == True and not self._cancel_export:
                self.TxtPercent.Text = "Generating Excel Drawing List..."
                self.do_events()
                selected_vms = [sv for sv in self.sheets if sv.IsSelected]
                if selected_vms:
                    try:
                        name_parts = []
                        for part in self.active_combined_scheme_parts:
                            sample_val = get_sample_value(doc, part.get("ParameterName", ""), None)
                            name_parts.append(part.get("Prefix", "") + sample_val + part.get("Suffix", "") + part.get("Separator", ""))
                        combined_name = "".join(name_parts).strip()
                        if not combined_name or combined_name == 'Combined_PDF': combined_name = None
                    except:
                        combined_name = None
                    generate_excel_transmittal(folder, selected_vms, doc, combined_name, self.active_combined_scheme_parts)

            if not self._cancel_export:
                theme = load_settings().get("theme", "Dark")
                
                done_items = [item for item in self.queue_items if item.Status == "Done"]
                error_items = [item for item in self.queue_items if item.Status == "Error"]
                skipped_items = [item for item in self.queue_items if item.Status == "Skipped"]
                
                if len(done_items) == total:
                    msg = "Export completed successfully."
                elif len(error_items) == total:
                    msg = "Export failed.\nAll files were open or encountered errors."
                elif len(skipped_items) == total:
                    msg = "Export skipped.\nNo files were exported."
                else:
                    msg = "Export finished with errors.\nSuccessfully exported: {}/{}\nFailed: {}\nSkipped: {}".format(
                        len(done_items), total, len(error_items), len(skipped_items)
                    )
                
                cw = CustomExportCompletedWindow(folder, msg, theme)
                cw.ShowDialog()
                
        except Exception as e:
            import traceback
            err_trace = traceback.format_exc()
            try:
                with open(r"c:\Users\User\Desktop\excel_error.txt", "w") as err_f:
                    err_f.write(err_trace)
            except:
                pass
            show_alert("An error occurred during export:\n{}".format(err_trace), is_error=True)
                    
        finally:
            self._exporting = False
            self._cancel_export = False
            self.BtnBack.IsEnabled = True
            self.BtnNext.IsEnabled = True
            self.BtnNext.Content = "Create"
            self.CloseBtn.IsEnabled = True


# ------------------------------------------------------------------------------
# Export Execution Logic
# ------------------------------------------------------------------------------
def export_dwg(folder, sheet, filename, dwg_setting):
    opt = DB.DWGExportOptions()
    if dwg_setting:
        opt = dwg_setting.GetDWGExportOptions()

    opt.MergedViews = True

    from System.Collections.Generic import List
    views = List[DB.ElementId]()
    views.Add(sheet.Id)

    doc.Export(folder, filename, views, opt)

def export_pdf_2022(folder, sheet, filename, zoom_type, zoom_pct):
    try:
        opt = DB.PDFExportOptions()
        opt.FileName = filename

        if zoom_type is not None:
            opt.ZoomType = zoom_type
        if zoom_pct is not None:
            opt.ZoomPercentage = zoom_pct

        from System.Collections.Generic import List
        views = List[DB.ElementId]()
        views.Add(sheet.Id)

        doc.Export(folder, views, opt)
        return True
    except Exception as e:
        import traceback
        show_alert("Failed to export PDF for sheet {}:\n{}".format(sheet.SheetNumber, traceback.format_exc()), is_error=True)
        return False

def export_combined_pdf_2022(folder, sheets, filename, zoom_type, zoom_pct):
    try:
        opt = DB.PDFExportOptions()
        opt.FileName = filename
        opt.Combine = True

        if zoom_type is not None:
            opt.ZoomType = zoom_type
        if zoom_pct is not None:
            opt.ZoomPercentage = zoom_pct

        from System.Collections.Generic import List
        views = List[DB.ElementId]()
        for sheet in sheets:
            views.Add(sheet.Id)

        doc.Export(folder, views, opt)
        return True
    except Exception as e:
        import traceback
        show_alert("Failed to export combined PDF:\n{}".format(traceback.format_exc()), is_error=True)
        return False

# ------------------------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------------------------
def main():
    global doc, uidoc
    uidoc = __revit__.ActiveUIDocument
    doc = uidoc.Document

    sheets = DB.FilteredElementCollector(doc)\
               .OfCategory(DB.BuiltInCategory.OST_Sheets)\
               .WhereElementIsNotElementType()\
               .ToElements()

    views_collector = DB.FilteredElementCollector(doc)\
                        .OfCategory(DB.BuiltInCategory.OST_Views)\
                        .WhereElementIsNotElementType()\
                        .ToElements()
    views = [v for v in views_collector if not v.IsTemplate and v.CanBePrinted]

    if not sheets and not views:
        show_alert("No Sheets or Views found in the current project.", is_warning=True)
    theme = load_settings().get("theme", "Dark")
    exp_name = "ExportUI_Light.xaml" if theme == "Light" else "ExportUI.xaml"
    xaml_path = os.path.join(os.path.dirname(__file__), exp_name)
    form = ExportManagerForm(xaml_path, sheets, views)
    form.ShowDialog()

def generate_excel_transmittal(folder, selected_vms, doc, combined_name=None, combined_parts=None):
    import os
    import re
    import time
    from Autodesk.Revit import DB

    def get_param_value(elem, param_name):
        if not elem: return ""
        p = elem.LookupParameter(param_name)
        if p and p.HasValue:
            return p.AsString() or p.AsValueString() or ""
        return ""

    try:
        # Find a valid sheet that is not the cover page
        first_sheet = None
        for vm in selected_vms:
            if vm.Sheet:
                name_lower = vm.Sheet.Name.lower() if vm.Sheet.Name else ""
                num_lower = vm.Sheet.SheetNumber.lower() if vm.Sheet.SheetNumber else ""
                if "cover" not in name_lower and "cover" not in num_lower:
                    first_sheet = vm.Sheet
                    break
        
        # Fallback to first sheet if only cover page is selected
        if not first_sheet and selected_vms:
            first_sheet = selected_vms[0].Sheet

        pi = doc.ProjectInformation
        tb = None
        if first_sheet:
            from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory
            tbs = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).OwnedByView(first_sheet.Id).ToElements()
            if tbs: tb = tbs[0]
            
        def get_best_param(param_name, fallback_name=None):
            val = get_param_value(first_sheet, param_name)
            if val: return val
            if fallback_name:
                val = get_param_value(first_sheet, fallback_name)
                if val: return val
                
            val = get_param_value(tb, param_name)
            if val: return val
            if fallback_name:
                val = get_param_value(tb, fallback_name)
                if val: return val
                
            val = get_param_value(pi, param_name)
            if val: return val
            if fallback_name:
                return get_param_value(pi, fallback_name)
            return ""

        def get_val_from_scheme(target_name):
            if combined_parts:
                for part in combined_parts:
                    p_name = part.get("ParameterName", "")
                    if target_name.lower() in p_name.lower():
                        val = get_best_param(p_name)
                        if val: return val
            return None

        # Project name, Building name taken from combined parameter if possible
        b_name_scheme = get_val_from_scheme("Building Name")
        p_name_scheme = get_val_from_scheme("Project Name") or get_val_from_scheme("Project Number")

        # Collect Info from RYN_PrInfo_ parameters (Sheet first, then Title Block, then Project Info)
        proj_number    = get_best_param("RYN_PrInfo_ProjectNumber", "Project Number")
        proj_name      = p_name_scheme if p_name_scheme else get_best_param("RYN_PrInfo_ProjectName", "Project Name")
        building_name  = b_name_scheme if b_name_scheme else (get_best_param("RYN_PrInfo_BuildingName", "Building Name") or proj_name)
        building_code  = get_best_param("RYN_PrInfo_BuildingCode", "Building Code")
        architect      = get_best_param("RYN_PrInfo_Architect", "Architect")
        civil_eng      = get_best_param("RYN_PrInfo_CivilEngineer", "Civil Engineer")
        mep_eng        = get_best_param("RYN_PrInfo_MepEngineer", "MEP Engineer")
        int_designer   = get_best_param("RYN_PrInfo_Int.Designer", "Int. Designer")
        infra_designer = get_best_param("RYN_PrInfo_Infra.Designer", "Infra. Designer")
        drawn_by       = get_best_param("RYN_PrInfo_DrawnBy", "Drawn By")
        checked_by     = get_best_param("RYN_PrInfo_CheckedBy", "Checked By")
        approved_by    = get_best_param("RYN_PrInfo_ApprovedBy", "Approved By")
        
        client         = get_best_param("RYN_PrInfo_Client", "Client")
        developer      = get_best_param("RYN_PrInfo_Developer", "Developer")
        atoll          = get_best_param("RYN_PrInfo_Atoll", "Atoll")
        island         = get_best_param("RYN_PrInfo_Island", "Island")
        lagoon         = get_best_param("RYN_PrInfo_Lagoon(GPSCOORD)", "Lagoon") or get_best_param("Lagoon (GPS Coordinates)")
        issued_for     = get_best_param("RYN_PrInfo_IssuedFor", "Issued For")
        issued_date    = get_best_param("RYN_PrInfo_IssuedDate", "Issued Date") or get_best_param("Project Issue Date")
        b_num          = get_best_param("RYN_PrInfo_BuildingNumber", "Building Number")
        discipline     = get_best_param("RYN_PrInfo_Discipline", "Discipline")
        
        if not client: client = get_best_param("Client Name")
        
        if combined_name:
            base_name = combined_name
        else:
            name_parts = []
            if proj_number: name_parts.append(proj_number + "-RYN-")
            if b_num: name_parts.append(b_num + "-")
            if building_code: name_parts.append(building_code + "-")
            if discipline: name_parts.append(discipline + "-")
            if building_name: name_parts.append(building_name)
            
            base_name = "".join(name_parts)
            if not base_name:
                base_name = "Export"
            
        safe_base = re.sub(r'[\\/*?:"<>|]', '_', base_name)
        filename = u"{} - LIST OF DRAWINGS.doc".format(safe_base)
        full_path = os.path.join(folder, filename)

        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except:
                filename = u"{}_{} - LIST OF DRAWINGS.doc".format(safe_base, int(time.time()))
                full_path = os.path.join(folder, filename)

        # Collect sheets by group
        groups = {}
        for vm in selected_vms:
            sheet = vm.Sheet
            grp = get_param_value(sheet, "Sheet Collection")
            if not grp: grp = "General"
            if grp not in groups:
                groups[grp] = []
            groups[grp].append(sheet)

        # Build HTML Content
        html = [
            u'<html xmlns:o="urn:schemas-microsoft-com:office:office"',
            u'xmlns:w="urn:schemas-microsoft-com:office:word"',
            u'xmlns="http://www.w3.org/TR/REC-html40">',
            u'<head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>',
            u'<style>',
            u'@page Section1 { size: 21cm 29.7cm; margin: 0.5cm 0.5cm 0.5cm 0.5cm; } div.Section1 { page: Section1; }',
            u'body { font-family: Calibri, sans-serif; font-size: 10pt; }',
            u'table { border-collapse: collapse; width: 100%; margin-bottom: 0px; margin-left: 0; margin-right: 0; }',
            u'td { border: 1px solid #999; padding: 2px 4px; }',
            u'.info-label { font-weight: bold; background-color: #f0f0f0; width: 25%; }',
            u'.info-value { }',
            u'.section-title { font-weight: bold; font-size: 10pt; background-color: #d9d9d9; padding: 4px 6px; }',
            u'.col-header { font-weight: bold; background-color: #D9D9D9; color: #000; text-align: center; border: 1px solid #666; }',
            u'.col-num { width: 15%; text-align: left; }',
            u'.col-name { width: 45%; }',
            u'.col-rev { width: 10%; text-align: center; }',
            u'.col-date { width: 12%; text-align: center; }',
            u'.col-size { width: 6%; text-align: center; }',
            u'</style></head><body><div class="Section1">',
            u'<table width="100%">\n        '
        ]

        # Get logo path dynamically
        try:
            import inspect
            script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
            logo_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "About.panel", "About.pushbutton", "logo.png")
            logo_uri = "file:///" + logo_path.replace("\\", "/")
        except:
            logo_path = ""
            logo_uri = ""
        
        # General Project Info Block - all from RYN_PrInfo_ parameters
        html.append(u'<tr>')
        html.append(u'<td colspan="2" style="text-align: center; padding: 15px; border: none;">')
        html.append(u'<table style="margin: 0 auto; border: none; width: auto;"><tr>')
        if logo_path and os.path.exists(logo_path):
            html.append(u'<td style="border: none; padding-right: 15px; vertical-align: middle;"><img src="{}" style="height: 40px; width: auto;" /></td>'.format(logo_uri))
        html.append(u'<td style="border: none; vertical-align: middle; font-size: 22pt; font-weight: bold; color: #802F2D;">RIYAN PRIVATE LIMITED</td>')
        html.append(u'</tr></table>')
        html.append(u'</td>')
        html.append(u'</tr>')
        html.append(u'<tr><td colspan="2" style="border: none; height: 3px; background-color: #802F2D;"></td></tr>')
        html.append(u'<tr><td colspan="2" style="border: none; height: 10px;"></td></tr>')
        
        html.append(u'<tr><td colspan="2" class="section-title" style="text-align: center; font-size: 12pt;">CONSULTANT PROJECT NO. {}</td></tr>'.format(proj_number))
        html.append(u'<tr><td colspan="2" style="border: none; height: 10px;"></td></tr>')
        
        html.append(u'<tr><td colspan="2" class="section-title">PROJECT NAME</td></tr>')
        html.append(u'<tr><td colspan="2" style="font-size: 14pt; font-weight: bold; padding: 8px;">{}</td></tr>'.format(proj_name))
        
        html.append(u'<tr><td class="info-label">CLIENT</td><td class="info-value">{}</td></tr>'.format(client))
        html.append(u'<tr><td class="info-label">DEVELOPER</td><td class="info-value">{}</td></tr>'.format(developer))
        html.append(u'<tr><td class="info-label">ATOLL</td><td class="info-value">{}</td></tr>'.format(atoll))
        html.append(u'<tr><td class="info-label">ISLAND</td><td class="info-value">{}</td></tr>'.format(island))
        html.append(u'<tr><td class="info-label">LAGOON (GPS COORDINATES)</td><td class="info-value">{}</td></tr>'.format(lagoon))
        
        html.append(u'<tr><td colspan="2" style="border: none; height: 12px;"></td></tr>')
        html.append(u'<tr><td class="info-label">ISSUED FOR</td><td style="font-size: 13pt; font-weight: bold;">{}</td></tr>'.format(issued_for))
        
        html.append(u'<tr><td colspan="2" style="border: none; height: 12px;"></td></tr>')
        html.append(u'<tr><td colspan="2" class="section-title">BUILDING NAME</td></tr>')
        html.append(u'<tr><td colspan="2" style="font-size: 14pt; font-weight: bold; padding: 8px;">{}</td></tr>'.format(building_name))
        html.append(u'<tr><td colspan="2" style="border: none; height: 12px;"></td></tr>')
        html.append(u'</table>\n')

        html.append(u'<table width="100%">')
        html.append(u'<tr>')
        html.append(u'<td class="col-header col-num">SHEET NUMBER</td>')
        html.append(u'<td class="col-header col-name">Sheet Name</td>')
        html.append(u'<td class="col-header col-rev">Revision</td>')
        html.append(u'<td class="col-header col-date">Rev. Date</td>')
        html.append(u'<td class="col-header col-date">Issue Date</td>')
        html.append(u'<td class="col-header col-size">Size</td>')
        html.append(u'</tr>')

        for grp in sorted(groups.keys()):
            html.append(u'<tr><td colspan="6" style="background-color: #e6e6e6; font-weight: bold; padding-top: 6px;">{}</td></tr>'.format(grp))
            
            sorted_sheets = sorted(groups[grp], key=lambda x: x.SheetNumber)
            row_num = 1
            for sheet in sorted_sheets:
                rev_num = ""
                rev_date = ""
                try:
                    rev_id = sheet.GetCurrentRevision()
                    if rev_id != DB.ElementId.InvalidElementId:
                        rev_el = doc.GetElement(rev_id)
                        if rev_el:
                            p_num = rev_el.get_Parameter(DB.BuiltInParameter.PROJECT_REVISION_SEQUENCE_NUM)
                            p_date = rev_el.get_Parameter(DB.BuiltInParameter.PROJECT_REVISION_REVISION_DATE)
                            if p_num and p_num.HasValue: rev_num = p_num.AsString() or ""
                            if p_date and p_date.HasValue: rev_date = p_date.AsString() or ""
                except:
                    pass
                if not rev_num:
                    try:
                        p = sheet.get_Parameter(DB.BuiltInParameter.SHEET_CURRENT_REVISION)
                        if p and p.HasValue:
                            rev_num = p.AsString() or ""
                    except:
                        pass
                if not rev_date:
                    try:
                        p = sheet.get_Parameter(DB.BuiltInParameter.SHEET_CURRENT_REVISION_DATE)
                        if p and p.HasValue:
                            rev_date = p.AsString() or ""
                    except:
                        pass

                issue_date = issued_date
                if not issue_date:
                    try:
                        p = sheet.get_Parameter(DB.BuiltInParameter.SHEET_ISSUE_DATE)
                        if p and p.HasValue:
                            issue_date = p.AsString() or ""
                    except:
                        pass
                
                html.append(u'<tr>')
                html.append(u'<td class="col-num">{}</td>'.format(sheet.SheetNumber.upper()))
                html.append(u'<td class="col-name">{}</td>'.format(sheet.Name))
                html.append(u'<td class="col-rev">{}</td>'.format(rev_num))
                html.append(u'<td class="col-date">{}</td>'.format(rev_date))
                html.append(u'<td class="col-date">{}</td>'.format(issue_date))
                html.append(u'<td class="col-size">A1</td>')
                html.append(u'</tr>')
                row_num += 1
                
            html.append(u'<tr><td colspan="6" style="border: none; height: 12px;"></td></tr>')
            
        html.append(u'</table></div></body></html>')
        
        with open(full_path, "wb") as f:
            f.write(u"\n".join(html).encode("utf-8"))

        return True

    except Exception as ex:
        import traceback
        err_msg = "Error generating Excel Transmittal:\n{}".format(traceback.format_exc())
        raise Exception(err_msg)

if __name__ == '__main__':
    main()








