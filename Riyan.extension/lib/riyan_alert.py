# -*- coding: utf-8 -*-
"""
Riyan Custom Alert & Dialog System
Centralized dark/light theme-adaptive modal dialogs for all Riyan pyRevit tools.
Complies strictly with the Custom UI & Dialog Styling Guardrails (Zero Default UI).
"""

import os
import sys
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
from System.Windows.Input import MouseButton, Key

def get_current_theme():
    """Detects current user theme preference from Revit API or settings."""
    try:
        from Autodesk.Revit.UI import UIThemeManager, UITheme
        if hasattr(UIThemeManager, "CurrentTheme"):
            if UIThemeManager.CurrentTheme == UITheme.Light:
                return "Light"
            elif UIThemeManager.CurrentTheme == UITheme.Dark:
                return "Dark"
    except Exception:
        pass

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

        if is_light:
            bg = "#FFFFFF"
            tb_bg = "#F8FAFC"
            footer_bg = "#F8FAFC"
            border = "#CBD5E1"
            footer_border = "#E2E8F0"
            fg_title = "#0F172A"
            fg_msg = "#0F172A"
            fg_details = "#334155"
            card_bg = "#F1F5F9"
            card_border = "#E2E8F0"
            close_fg = "#64748B"
            accent_color = "#C0272D"
            btn_bg = "#C0272D"
            btn_hover = "#D32F2F"
        else:
            bg = "#2D2D30"
            tb_bg = "#1E1E1E"
            footer_bg = "#1E1E1E"
            border = "#3F3F46"
            footer_border = "#38383D"
            fg_title = "#FFFFFF"
            fg_msg = "#FFFFFF"
            fg_details = "#D1D5DB"
            card_bg = "#222225"
            card_border = "#38383D"
            close_fg = "#A1A1AA"
            accent_color = "#C0272D"
            btn_bg = "#C0272D"
            btn_hover = "#D32F2F"

        if is_error:
            icon_char = u"&#x2715;"
            icon_color = "#EF4444"
            badge_bg = "#33EF4444"
            badge_border = "#EF4444"
        elif is_warning:
            icon_char = u"&#x26A0;"
            icon_color = "#F59E0B"
            badge_bg = "#33F59E0B"
            badge_border = "#F59E0B"
        else:
            icon_char = u"&#x2713;"
            icon_color = "#10B981"
            badge_bg = "#2210B981"
            badge_border = "#10B981"

        # Split message into headline and optional structured details
        clean_msg = (message or "").strip()
        lines = clean_msg.split("\n", 1)
        headline = lines[0].strip()
        details = lines[1].strip() if len(lines) > 1 else ""

        headline_escaped = headline.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        title_escaped = (title or "Riyan Tools").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

        details_block = ""
        if details:
            details_escaped = details.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            details_block = """
                    <Border Background="{card_bg}" BorderBrush="{card_border}" BorderThickness="1" CornerRadius="6" Padding="12,10" Margin="0,10,0,0">
                        <TextBlock Text="{details}" Foreground="{fg_details}" FontSize="12" FontFamily="Segoe UI" LineHeight="18" TextWrapping="Wrap"/>
                    </Border>
            """.format(card_bg=card_bg, card_border=card_border, details=details_escaped, fg_details=fg_details)

        xaml_code = """<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="{title}" Width="450" SizeToContent="Height"
        WindowStartupLocation="CenterScreen" ShowInTaskbar="False"
        Background="Transparent" WindowStyle="None" AllowsTransparency="True"
        ResizeMode="NoResize" Topmost="True">
    <Border Background="{bg}" BorderBrush="{border}" BorderThickness="1.5" CornerRadius="10">
        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="38"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="50"/>
            </Grid.RowDefinitions>

            <!-- Title Bar -->
            <Border Grid.Row="0" Background="{tb_bg}" CornerRadius="9,9,0,0" x:Name="TitleBar">
                <Grid>
                    <StackPanel Orientation="Horizontal" VerticalAlignment="Center" Margin="14,0,0,0">
                        <TextBlock Text="&#x25CF;" FontFamily="Segoe UI Symbol" Foreground="{accent_color}" FontSize="11" VerticalAlignment="Center" Margin="0,0,8,0"/>
                        <TextBlock Text="{title}" Foreground="{fg_title}" FontSize="12" FontWeight="SemiBold" VerticalAlignment="Center"/>
                    </StackPanel>
                    <Button x:Name="CloseBtn" Content="&#x2715;" HorizontalAlignment="Right"
                            Width="40" Height="38" BorderThickness="0" Cursor="Hand"
                            Background="Transparent" Foreground="{close_fg}"
                            FontSize="12">
                        <Button.Template>
                            <ControlTemplate TargetType="Button">
                                <Border x:Name="bd" Background="Transparent" CornerRadius="0,9,0,0">
                                    <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                                </Border>
                                <ControlTemplate.Triggers>
                                    <Trigger Property="IsMouseOver" Value="True">
                                        <Setter TargetName="bd" Property="Background" Value="#DC2626"/>
                                        <Setter Property="Foreground" Value="White"/>
                                    </Trigger>
                                </ControlTemplate.Triggers>
                            </ControlTemplate>
                        </Button.Template>
                    </Button>
                </Grid>
            </Border>

            <!-- Content Area -->
            <Grid Grid.Row="1" Margin="20,18,20,18">
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="Auto"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>

                <!-- Status Badge -->
                <Border Grid.Column="0" Width="36" Height="36" CornerRadius="18" 
                        Background="{badge_bg}" BorderBrush="{badge_border}" BorderThickness="1.5" 
                        VerticalAlignment="Top" Margin="0,2,16,0">
                    <TextBlock Text="{icon_char}" Foreground="{icon_color}" FontSize="17" 
                               FontWeight="Bold" HorizontalAlignment="Center" VerticalAlignment="Center"/>
                </Border>

                <!-- Message Stack -->
                <StackPanel Grid.Column="1" VerticalAlignment="Center">
                    <TextBlock Text="{headline}" Foreground="{fg_msg}" 
                               FontSize="13" FontWeight="SemiBold" LineHeight="19" TextWrapping="Wrap"/>
                    {details_block}
                </StackPanel>
            </Grid>

            <!-- Footer -->
            <Border Grid.Row="2" Background="{footer_bg}" BorderBrush="{footer_border}" BorderThickness="0,1,0,0" CornerRadius="0,0,9,9">
                <Button x:Name="OkBtn" Content="OK" HorizontalAlignment="Right" Width="84" Height="28" 
                        Margin="0,0,14,0" Cursor="Hand" Foreground="White" FontWeight="Bold" FontSize="11.5" 
                        IsDefault="True" IsCancel="True">
                    <Button.Template>
                        <ControlTemplate TargetType="Button">
                            <Border x:Name="bd" Background="{btn_bg}" CornerRadius="5">
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
            badge_bg=badge_bg,
            badge_border=badge_border,
            icon_char=icon_char,
            icon_color=icon_color,
            headline=headline_escaped,
            fg_msg=fg_msg,
            details_block=details_block,
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

        self.win.PreviewKeyDown += self._on_preview_key_down

    def _on_preview_key_down(self, sender, e):
        if e.Key == Key.Escape:
            e.Handled = True
            self.win.Close()

    def _on_close(self, sender, e):
        self.win.Close()

    def _on_drag(self, sender, e):
        try:
            if e.ChangedButton == MouseButton.Left:
                self.win.DragMove()
        except Exception:
            pass

    def ShowDialog(self):
        try:
            self.win.Topmost = True
            # Set Revit window as owner via Win32 HWND if available
            from pyrevit import revit
            if hasattr(revit, "HOST_APP") and hasattr(revit.HOST_APP, "proc_window") and revit.HOST_APP.proc_window:
                helper = WindowInteropHelper(self.win)
                helper.Owner = revit.HOST_APP.proc_window
            else:
                app_windows = Application.Current.Windows if Application.Current else None
                if app_windows and app_windows.Count > 0:
                    self.win.Owner = app_windows[0]
        except Exception:
            pass
        return self.win.ShowDialog()

def show_alert(message, title="Riyan Tools", is_error=False, is_warning=False, theme=None):
    """
    Displays the signature Custom WPF Alert Modal.
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
