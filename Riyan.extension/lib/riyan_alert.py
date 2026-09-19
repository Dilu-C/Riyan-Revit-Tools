# -*- coding: utf-8 -*-
"""
Riyan Custom Alert & Dialog System
Centralized dark/light theme-adaptive modal dialogs for all Riyan pyRevit tools.
Complies strictly with the Riyan Custom UI & Dialog Styling Rule (Zero Default UI).
"""

import os
import clr

clr.AddReference("System")
clr.AddReference("System.Xml")
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")

import System
from System.Windows import Window, Application, WindowStartupLocation, WindowStyle, ResizeMode
from System.Windows.Markup import XamlReader
from System.Windows.Interop import WindowInteropHelper
from System.Windows.Input import MouseButton

def get_current_theme():
    """Detects current user theme preference from central settings or environment."""
    try:
        import json
        settings_path = os.path.expandvars(r"%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools\settings.json")
        if os.path.exists(settings_path):
            with open(settings_path, "r") as f:
                data = json.load(f)
                return data.get("theme", "Dark")
    except Exception:
        pass
    return "Dark"

class CustomAlertWindow(object):
    def __init__(self, message, title="Riyan Tools", is_error=False, is_warning=False, theme=None):
        if theme is None:
            theme = get_current_theme()
        is_light = (theme == "Light")

        bg = "#FFFFFF" if is_light else "#18181B"
        tb_bg = "#F4F4F5" if is_light else "#202024"
        footer_bg = "#FAFAFA" if is_light else "#141416"
        border = "#E4E4E7" if is_light else "#2E2E33"
        footer_border = "#E4E4E7" if is_light else "#27272A"
        fg_title = "#18181B" if is_light else "#F4F4F5"
        fg_msg = "#27272A" if is_light else "#E4E4E7"
        close_fg = "#71717A" if is_light else "#A1A1AA"

        if is_error:
            icon_char = u"✖"
            icon_color = "#DC2626" if is_light else "#EF4444"
            badge_title = "Error"
        elif is_warning:
            icon_char = u"⚠"
            icon_color = "#D97706" if is_light else "#F59E0B"
            badge_title = "Warning"
        else:
            icon_char = u"✔"
            icon_color = "#16A34A" if is_light else "#10B981"
            badge_title = "Success"

        accent_color = "#802F2D"
        btn_bg = "#802F2D"
        btn_hover = "#661F1D" if is_light else "#9E3A38"

        # XML-safe escaping
        msg_escaped = (message or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        title_escaped = (title or "Riyan Tools").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

        xaml_code = """<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="{title}" Width="440" SizeToContent="Height"
        WindowStartupLocation="CenterScreen" 
        Background="{bg}" WindowStyle="None" AllowsTransparency="False"
        ResizeMode="NoResize">
    <Border BorderBrush="{border}" BorderThickness="1.5" CornerRadius="8">
        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="38"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="48"/>
            </Grid.RowDefinitions>

            <!-- Title Bar -->
            <Grid x:Name="TitleBar" Grid.Row="0" Background="{tb_bg}">
                <StackPanel Orientation="Horizontal" VerticalAlignment="Center" Margin="14,0,0,0">
                    <TextBlock Text="■" Foreground="{accent_color}" FontSize="12" VerticalAlignment="Center" Margin="0,0,8,0"/>
                    <TextBlock Text="{title}" Foreground="{fg_title}" FontSize="12" FontWeight="SemiBold" VerticalAlignment="Center"/>
                </StackPanel>
                <Button x:Name="CloseBtn" Content="✕" HorizontalAlignment="Right"
                        Width="40" Height="38" BorderThickness="0" Cursor="Hand"
                        Background="Transparent" Foreground="{close_fg}"
                        FontSize="12">
                    <Button.Template>
                        <ControlTemplate TargetType="Button">
                            <Border x:Name="bd" Background="Transparent">
                                <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                            </Border>
                            <ControlTemplate.Triggers>
                                <Trigger Property="IsMouseOver" Value="True">
                                    <Setter TargetName="bd" Property="Background" Value="#802F2D"/>
                                    <Setter Property="Foreground" Value="White"/>
                                </Trigger>
                            </ControlTemplate.Triggers>
                        </ControlTemplate>
                    </Button.Template>
                </Button>
            </Grid>

            <!-- Content Area -->
            <Grid Grid.Row="1" Margin="20,18,20,18">
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="Auto"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>

                <TextBlock Grid.Column="0" Text="{icon_char}" Foreground="{icon_color}" FontSize="24" 
                           FontWeight="Bold" VerticalAlignment="Top" Margin="0,0,16,0"/>

                <TextBlock Grid.Column="1" Text="{msg}" Foreground="{fg_msg}" 
                           FontSize="12.5" LineHeight="19" TextWrapping="Wrap" VerticalAlignment="Center" HorizontalAlignment="Left"/>
            </Grid>

            <!-- Footer -->
            <Border Grid.Row="2" Background="{footer_bg}" BorderBrush="{footer_border}" BorderThickness="0,1,0,0">
                <Button x:Name="OkBtn" Content="OK" HorizontalAlignment="Right" Width="84" Height="28" 
                        Margin="0,0,14,0" Cursor="Hand" Foreground="White" FontWeight="Bold" FontSize="11.5" IsDefault="True" IsCancel="True">
                    <Button.Template>
                        <ControlTemplate TargetType="Button">
                            <Border x:Name="bd" Background="{btn_bg}" CornerRadius="4">
                                <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                            </Border>
                            <ControlTemplate.Triggers>
                                <Trigger Property="IsMouseOver" Value="True">
                                    <Setter TargetName="bd" Property="Background" Value="{btn_hover}"/>
                                </Trigger>
                            </ControlTemplate.Triggers>
                        </ControlTemplate>
                    </Button.Template>
                </Button>
            </Border>
        </Grid>
    </Border>
</Window>""".format(
            title=title_escaped,
            bg=bg,
            border=border,
            tb_bg=tb_bg,
            accent_color=accent_color,
            fg_title=fg_title,
            close_fg=close_fg,
            icon_char=icon_char,
            icon_color=icon_color,
            msg=msg_escaped,
            fg_msg=fg_msg,
            footer_bg=footer_bg,
            footer_border=footer_border,
            btn_bg=btn_bg,
            btn_hover=btn_hover
        )

        self.win = XamlReader.Parse(xaml_code)
        
        # Attach event handlers
        close_btn = self.win.FindName("CloseBtn")
        if close_btn:
            close_btn.Click += self._on_close
        ok_btn = self.win.FindName("OkBtn")
        if ok_btn:
            ok_btn.Click += self._on_close
        title_bar = self.win.FindName("TitleBar")
        if title_bar:
            title_bar.MouseLeftButtonDown += self._on_drag

    def _on_close(self, sender, e):
        self.win.Close()

    def _on_drag(self, sender, e):
        try:
            if e.ChangedButton == MouseButton.Left:
                self.win.DragMove()
        except:
            pass

    def ShowDialog(self):
        try:
            # Set Revit window as owner if available
            app_windows = Application.Current.Windows if Application.Current else None
            if app_windows and app_windows.Count > 0:
                self.win.Owner = app_windows[0]
        except Exception:
            pass
        return self.win.ShowDialog()

def show_alert(message, title="Riyan Tools", is_error=False, is_warning=False, theme=None):
    """
    Displays the signature Riyan Custom WPF Alert Modal.
    Strictly replaces TaskDialog.Show and forms.alert across the entire extension.
    """
    try:
        dlg = CustomAlertWindow(message, title=title, is_error=is_error, is_warning=is_warning, theme=theme)
        return dlg.ShowDialog()
    except Exception:
        # Emergency fallback without crash
        try:
            from pyrevit import forms
            forms.alert(message, title=title)
        except Exception:
            pass
