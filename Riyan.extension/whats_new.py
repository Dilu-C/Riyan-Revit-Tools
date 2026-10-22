# -*- coding: utf-8 -*-
import os
import sys
import clr
try:
    clr.AddReference('PresentationFramework')
    clr.AddReference('PresentationCore')
    clr.AddReference('WindowsBase')
except Exception:
    pass

from pyrevit import forms
import System

XAML_STRING = """
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="What's New in Riyan Tools - {VERSION}" Height="630" Width="940"
        WindowStartupLocation="CenterScreen"
        Background="Transparent" WindowStyle="None" AllowsTransparency="True"
        ResizeMode="NoResize" FontFamily="Segoe UI">

    <Window.Resources>
        <SolidColorBrush x:Key="WindowBg" Color="#1C1C20"/>
        <SolidColorBrush x:Key="HeaderBg" Color="#222227"/>
        <SolidColorBrush x:Key="CardBg" Color="#24242A"/>
        <SolidColorBrush x:Key="CardBorder" Color="#383842"/>
        <SolidColorBrush x:Key="ItemBg" Color="#1D1D22"/>
        <SolidColorBrush x:Key="ItemBorder" Color="#30303A"/>
        <SolidColorBrush x:Key="PrimaryMaroon" Color="#802F2D"/>
        <SolidColorBrush x:Key="PrimaryHover" Color="#A13B38"/>
        <SolidColorBrush x:Key="EmeraldText" Color="#34D399"/>
        <SolidColorBrush x:Key="EmeraldBg" Color="#132B20"/>
        <SolidColorBrush x:Key="BlueText" Color="#60A5FA"/>
        <SolidColorBrush x:Key="BlueBg" Color="#1A283D"/>
        <SolidColorBrush x:Key="PurpleText" Color="#C084FC"/>
        <SolidColorBrush x:Key="PurpleBg" Color="#2A1E38"/>
        <SolidColorBrush x:Key="TextWhite" Color="#FFFFFF"/>
        <SolidColorBrush x:Key="TextPrimary" Color="#F3F4F6"/>
        <SolidColorBrush x:Key="TextMuted" Color="#9CA3AF"/>
        <SolidColorBrush x:Key="TextDarkMuted" Color="#6B7280"/>

        <Style x:Key="PrimaryBtn" TargetType="Button">
            <Setter Property="Background" Value="{StaticResource PrimaryMaroon}"/>
            <Setter Property="Foreground" Value="White"/>
            <Setter Property="FontWeight" Value="Bold"/>
            <Setter Property="FontSize" Value="13"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border x:Name="border" Background="{TemplateBinding Background}" CornerRadius="8" Padding="20,9">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter TargetName="border" Property="Background" Value="{StaticResource PrimaryHover}"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>

        <Style x:Key="CloseBtnStyle" TargetType="Button">
            <Setter Property="Background" Value="Transparent"/>
            <Setter Property="Foreground" Value="#9CA3AF"/>
            <Setter Property="FontSize" Value="13"/>
            <Setter Property="FontWeight" Value="SemiBold"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="BorderThickness" Value="0"/>
            <Setter Property="Padding" Value="0"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border x:Name="bd" Background="{TemplateBinding Background}" CornerRadius="0,11,0,0">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter TargetName="bd" Property="Background" Value="#DC2626"/>
                                <Setter Property="Foreground" Value="White"/>
                            </Trigger>
                            <Trigger Property="IsPressed" Value="True">
                                <Setter TargetName="bd" Property="Background" Value="#991B1B"/>
                                <Setter Property="Foreground" Value="White"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>
    </Window.Resources>

    <Border Background="{StaticResource WindowBg}" CornerRadius="12" BorderBrush="#4B5563" BorderThickness="1">
        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="40"/>
                <RowDefinition Height="Auto"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="58"/>
            </Grid.RowDefinitions>

            <!-- Custom Draggable Title Bar -->
            <Border x:Name="TitleBar" Grid.Row="0" Background="#141417" CornerRadius="11,11,0,0" BorderBrush="#2D2D35" BorderThickness="0,0,0,1">
                <Grid>
                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="*"/>
                        <ColumnDefinition Width="42"/>
                    </Grid.ColumnDefinitions>
                    <StackPanel Orientation="Horizontal" VerticalAlignment="Center" Margin="16,0,0,0">
                        <TextBlock Text="What's New in Riyan Tools" Foreground="#9CA3AF" FontSize="12" FontWeight="SemiBold"/>
                        <TextBlock Text=" — Release Highlights &amp; Migration Guide" Foreground="#6B7280" FontSize="12" Margin="4,0,0,0"/>
                    </StackPanel>
                    <Button x:Name="BtnCloseX" Grid.Column="1" Content="✕" Style="{StaticResource CloseBtnStyle}"/>
                </Grid>
            </Border>

            <!-- Header Section -->
            <Border Grid.Row="1" Background="{StaticResource HeaderBg}" BorderBrush="#2F2F38" BorderThickness="0,0,0,1" Padding="24,13">
                <Grid>
                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="54"/>
                        <ColumnDefinition Width="*"/>
                        <ColumnDefinition Width="Auto"/>
                    </Grid.ColumnDefinitions>

                    <!-- Icon / Brand Badge -->
                    <Border Grid.Column="0" Width="44" Height="44" CornerRadius="10" Background="{StaticResource PrimaryMaroon}" Margin="0,0,10,0">
                        <TextBlock Text="R" Foreground="White" FontSize="24" FontWeight="Black" HorizontalAlignment="Center" VerticalAlignment="Center"/>
                    </Border>

                    <!-- Title Info -->
                    <StackPanel Grid.Column="1" VerticalAlignment="Center">
                        <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                            <TextBlock Text="Riyan Revit Tools" Foreground="{StaticResource TextWhite}" FontSize="19" FontWeight="Black" Margin="0,0,10,0"/>
                            
                            <!-- Upgrade Pill -->
                            <Border Background="{StaticResource BlueBg}" BorderBrush="#2563EB" BorderThickness="1" CornerRadius="6" Padding="8,2" Margin="0,0,6,0">
                                <TextBlock Text="{PREV_VERSION} ➔ {VERSION}" Foreground="{StaticResource BlueText}" FontSize="11" FontWeight="Bold"/>
                            </Border>

                            <!-- Major Release Pill -->
                            <Border Background="{StaticResource EmeraldBg}" BorderBrush="#059669" BorderThickness="1" CornerRadius="6" Padding="8,2">
                                <TextBlock Text="MAJOR UPDATE" Foreground="{StaticResource EmeraldText}" FontSize="10" FontWeight="Bold"/>
                            </Border>
                        </StackPanel>
                        
                        <TextBlock Text="Multi-Discipline Family Library, Interactive Video Guides, Parameter Security &amp; Smart Export Automation." Foreground="{StaticResource TextMuted}" FontSize="11" Margin="0,4,0,2"/>
                        <TextBlock Text="Engineering Team: Asanka, Udarie, Chalana &amp; Dilupa" Foreground="{StaticResource TextDarkMuted}" FontSize="10" FontWeight="SemiBold"/>
                    </StackPanel>

                    <!-- Status Pill -->
                    <Border Grid.Column="2" Background="{StaticResource EmeraldBg}" BorderBrush="#059669" BorderThickness="1" CornerRadius="8" Padding="12,6" VerticalAlignment="Center">
                        <StackPanel Orientation="Horizontal">
                            <TextBlock Text="✓" Foreground="{StaticResource EmeraldText}" FontSize="12" FontWeight="Bold" Margin="0,0,6,0"/>
                            <TextBlock Text="100% Verified &amp; Active" Foreground="{StaticResource EmeraldText}" FontSize="11" FontWeight="Bold"/>
                        </StackPanel>
                    </Border>
                </Grid>
            </Border>

            <!-- 3 Categorized Columns -->
            <Grid Grid.Row="2" Margin="22,14,22,12">
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="14"/>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="14"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>

                <!-- COLUMN 1: WHAT'S NEW (ADDED) -->
                <Border Grid.Column="0" Background="{StaticResource CardBg}" BorderBrush="{StaticResource CardBorder}" BorderThickness="1" CornerRadius="10" Padding="13,12">
                    <Grid>
                        <Grid.RowDefinitions>
                            <RowDefinition Height="Auto"/>
                            <RowDefinition Height="*"/>
                        </Grid.RowDefinitions>

                        <!-- Column Header -->
                        <StackPanel Grid.Row="0" Margin="0,0,0,10">
                            <StackPanel Orientation="Horizontal" Margin="0,0,0,4">
                                <Border Background="{StaticResource EmeraldBg}" BorderBrush="#059669" BorderThickness="1" CornerRadius="4" Padding="6,2" Margin="0,0,6,0">
                                    <TextBlock Text="✨ NEW" Foreground="{StaticResource EmeraldText}" FontSize="9" FontWeight="Black"/>
                                </Border>
                                <TextBlock Text="What's Added" Foreground="{StaticResource TextWhite}" FontSize="13" FontWeight="Bold" VerticalAlignment="Center"/>
                            </StackPanel>
                            <TextBlock Text="Brand new tools and assets added to your ribbon" Foreground="{StaticResource TextMuted}" FontSize="10"/>
                        </StackPanel>

                        <!-- Items Stack -->
                        <StackPanel Grid.Row="1">
                            <!-- Item 1 -->
                            <Border Background="{StaticResource ItemBg}" BorderBrush="{StaticResource ItemBorder}" BorderThickness="1" CornerRadius="7" Padding="10" Margin="0,0,0,8">
                                <StackPanel>
                                    <TextBlock Text="100+ Multi-Discipline Families" Foreground="{StaticResource TextPrimary}" FontSize="11" FontWeight="Bold"/>
                                    <TextBlock Text="Ready-to-place Structural beams/columns, Plumbing fixtures, Fire Fighting &amp; ACMV diffusers in Riyan Library." Foreground="{StaticResource TextMuted}" FontSize="10" TextWrapping="Wrap" LineHeight="14" Margin="0,3,0,0"/>
                                </StackPanel>
                            </Border>

                            <!-- Item 2 -->
                            <Border Background="{StaticResource ItemBg}" BorderBrush="{StaticResource ItemBorder}" BorderThickness="1" CornerRadius="7" Padding="10" Margin="0,0,0,8">
                                <StackPanel>
                                    <TextBlock Text="Crisp 3D Thumbnail Previews" Foreground="{StaticResource TextPrimary}" FontSize="11" FontWeight="Bold"/>
                                    <TextBlock Text="Every family in the library displays clear 3D preview cards. Never load or guess wrong families again." Foreground="{StaticResource TextMuted}" FontSize="10" TextWrapping="Wrap" LineHeight="14" Margin="0,3,0,0"/>
                                </StackPanel>
                            </Border>

                            <!-- Item 3 -->
                            <Border Background="{StaticResource ItemBg}" BorderBrush="{StaticResource ItemBorder}" BorderThickness="1" CornerRadius="7" Padding="10">
                                <StackPanel>
                                    <TextBlock Text="Video Tooltips on Ribbon" Foreground="{StaticResource TextPrimary}" FontSize="11" FontWeight="Bold"/>
                                    <TextBlock Text="Hover over ribbon buttons to watch animated visual clips explaining how each tool works in seconds." Foreground="{StaticResource TextMuted}" FontSize="10" TextWrapping="Wrap" LineHeight="14" Margin="0,3,0,0"/>
                                </StackPanel>
                            </Border>
                        </StackPanel>
                    </Grid>
                </Border>

                <!-- COLUMN 2: WHAT'S IMPROVED (UPGRADES) -->
                <Border Grid.Column="2" Background="{StaticResource CardBg}" BorderBrush="{StaticResource CardBorder}" BorderThickness="1" CornerRadius="10" Padding="13,12">
                    <Grid>
                        <Grid.RowDefinitions>
                            <RowDefinition Height="Auto"/>
                            <RowDefinition Height="*"/>
                        </Grid.RowDefinitions>

                        <!-- Column Header -->
                        <StackPanel Grid.Row="0" Margin="0,0,0,10">
                            <StackPanel Orientation="Horizontal" Margin="0,0,0,4">
                                <Border Background="{StaticResource BlueBg}" BorderBrush="#2563EB" BorderThickness="1" CornerRadius="4" Padding="6,2" Margin="0,0,6,0">
                                    <TextBlock Text="⚡ UPGRADES" Foreground="{StaticResource BlueText}" FontSize="9" FontWeight="Black"/>
                                </Border>
                                <TextBlock Text="What's Improved" Foreground="{StaticResource TextWhite}" FontSize="13" FontWeight="Bold" VerticalAlignment="Center"/>
                            </StackPanel>
                            <TextBlock Text="Smoother workflow and major bug fixes" Foreground="{StaticResource TextMuted}" FontSize="10"/>
                        </StackPanel>

                        <!-- Items Stack -->
                        <StackPanel Grid.Row="1">
                            <!-- Item 1 -->
                            <Border Background="{StaticResource ItemBg}" BorderBrush="{StaticResource ItemBorder}" BorderThickness="1" CornerRadius="7" Padding="10" Margin="0,0,0,8">
                                <StackPanel>
                                    <TextBlock Text="Smart Batch &amp; Sheet Export" Foreground="{StaticResource TextPrimary}" FontSize="11" FontWeight="Bold"/>
                                    <TextBlock Text="Auto sheet revision naming, organized CAD/PDF folder structures, and zero Revit crashing during export loops." Foreground="{StaticResource TextMuted}" FontSize="10" TextWrapping="Wrap" LineHeight="14" Margin="0,3,0,0"/>
                                </StackPanel>
                            </Border>

                            <!-- Item 2 -->
                            <Border Background="{StaticResource ItemBg}" BorderBrush="{StaticResource ItemBorder}" BorderThickness="1" CornerRadius="7" Padding="10" Margin="0,0,0,8">
                                <StackPanel>
                                    <TextBlock Text="Auto-Linked Shared Parameters" Foreground="{StaticResource TextPrimary}" FontSize="11" FontWeight="Bold"/>
                                    <TextBlock Text="Revit automatically connects to the official company parameter file on startup. No missing parameter errors." Foreground="{StaticResource TextMuted}" FontSize="10" TextWrapping="Wrap" LineHeight="14" Margin="0,3,0,0"/>
                                </StackPanel>
                            </Border>

                            <!-- Item 3 -->
                            <Border Background="{StaticResource ItemBg}" BorderBrush="{StaticResource ItemBorder}" BorderThickness="1" CornerRadius="7" Padding="10">
                                <StackPanel>
                                    <TextBlock Text="Live SharePoint Library Sync" Foreground="{StaticResource TextPrimary}" FontSize="11" FontWeight="Bold"/>
                                    <TextBlock Text="When coordinators update families in SharePoint, they reflect live across all PCs with 1-click overwrite loading." Foreground="{StaticResource TextMuted}" FontSize="10" TextWrapping="Wrap" LineHeight="14" Margin="0,3,0,0"/>
                                </StackPanel>
                            </Border>
                        </StackPanel>
                    </Grid>
                </Border>

                <!-- COLUMN 3: WHAT'S CLEANED & PROTECTED -->
                <Border Grid.Column="4" Background="{StaticResource CardBg}" BorderBrush="{StaticResource CardBorder}" BorderThickness="1" CornerRadius="10" Padding="13,12">
                    <Grid>
                        <Grid.RowDefinitions>
                            <RowDefinition Height="Auto"/>
                            <RowDefinition Height="*"/>
                        </Grid.RowDefinitions>

                        <!-- Column Header -->
                        <StackPanel Grid.Row="0" Margin="0,0,0,10">
                            <StackPanel Orientation="Horizontal" Margin="0,0,0,4">
                                <Border Background="{StaticResource PurpleBg}" BorderBrush="#9333EA" BorderThickness="1" CornerRadius="4" Padding="6,2" Margin="0,0,6,0">
                                    <TextBlock Text="🛡️ OPTIMIZED" Foreground="{StaticResource PurpleText}" FontSize="9" FontWeight="Black"/>
                                </Border>
                                <TextBlock Text="Cleaned &amp; Protected" Foreground="{StaticResource TextWhite}" FontSize="13" FontWeight="Bold" VerticalAlignment="Center"/>
                            </StackPanel>
                            <TextBlock Text="Removed junk, lag, and potential errors" Foreground="{StaticResource TextMuted}" FontSize="10"/>
                        </StackPanel>

                        <!-- Items Stack -->
                        <StackPanel Grid.Row="1">
                            <!-- Item 1 -->
                            <Border Background="{StaticResource ItemBg}" BorderBrush="{StaticResource ItemBorder}" BorderThickness="1" CornerRadius="7" Padding="10" Margin="0,0,0,8">
                                <StackPanel>
                                    <TextBlock Text="Wiped Obsolete UI Caches" Foreground="{StaticResource TextPrimary}" FontSize="11" FontWeight="Bold"/>
                                    <TextBlock Text="Auto-purged stale pyRevit caches, duplicate parameter paths, and old script remnants to prevent conflicts." Foreground="{StaticResource TextMuted}" FontSize="10" TextWrapping="Wrap" LineHeight="14" Margin="0,3,0,0"/>
                                </StackPanel>
                            </Border>

                            <!-- Item 2 -->
                            <Border Background="{StaticResource ItemBg}" BorderBrush="{StaticResource ItemBorder}" BorderThickness="1" CornerRadius="7" Padding="10" Margin="0,0,0,8">
                                <StackPanel>
                                    <TextBlock Text="Zero Startup Delay (0.00s Lag)" Foreground="{StaticResource TextPrimary}" FontSize="11" FontWeight="Bold"/>
                                    <TextBlock Text="Heavy startup network queries were removed. pyRevit launches immediately with zero Revit slowdown." Foreground="{StaticResource TextMuted}" FontSize="10" TextWrapping="Wrap" LineHeight="14" Margin="0,3,0,0"/>
                                </StackPanel>
                            </Border>

                            <!-- Item 3 -->
                            <Border Background="{StaticResource ItemBg}" BorderBrush="{StaticResource ItemBorder}" BorderThickness="1" CornerRadius="7" Padding="10">
                                <StackPanel>
                                    <TextBlock Text="Locked Parameter Protection" Foreground="{StaticResource TextPrimary}" FontSize="11" FontWeight="Bold"/>
                                    <TextBlock Text="Standard users have Read-Only lock on parameter definitions, preventing accidental deletion or project file corruption." Foreground="{StaticResource TextMuted}" FontSize="10" TextWrapping="Wrap" LineHeight="14" Margin="0,3,0,0"/>
                                </StackPanel>
                            </Border>
                        </StackPanel>
                    </Grid>
                </Border>
            </Grid>

            <!-- Footer Bar -->
            <Border Grid.Row="3" Background="#141417" CornerRadius="0,0,11,11" Padding="24,0">
                <Grid>
                    <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                        <TextBlock Text="Engine Compatibility: " Foreground="{StaticResource TextDarkMuted}" FontSize="11"/>
                        <TextBlock Text="Revit 2021 – 2026 (Active Production) | 2027+ Ready" Foreground="{StaticResource EmeraldText}" FontSize="11" FontWeight="Bold"/>
                    </StackPanel>
                    <Button x:Name="BtnGotIt" Content="Got It, Let's Work! 🚀" Style="{StaticResource PrimaryBtn}" HorizontalAlignment="Right" VerticalAlignment="Center"/>
                </Grid>
            </Border>
        </Grid>
    </Border>
</Window>
"""

class WhatsNewWindow(forms.WPFWindow):
    def __init__(self, xaml_source, literal_string=True):
        forms.WPFWindow.__init__(self, xaml_source, literal_string=literal_string, handle_esc=True, set_owner=True)
        
        if hasattr(self, 'BtnClose') and self.BtnClose:
            self.BtnClose.Click += self.CloseBtn_Click
        if hasattr(self, 'BtnCloseX') and self.BtnCloseX:
            self.BtnCloseX.Click += self.CloseBtn_Click
        if hasattr(self, 'BtnGotIt') and self.BtnGotIt:
            self.BtnGotIt.Click += self.CloseBtn_Click
        if hasattr(self, 'TitleBar') and self.TitleBar:
            self.TitleBar.MouseLeftButtonDown += self.TitleBar_MouseDown
            
        try:
            self.PreviewKeyDown += self.Window_PreviewKeyDown
        except Exception:
            pass
            
    def Window_PreviewKeyDown(self, sender, e):
        try:
            if e.Key == System.Windows.Input.Key.Escape:
                e.Handled = True
                self.Close()
        except Exception:
            pass
            
    def CloseBtn_Click(self, sender, e):
        self.Close()
        
    def TitleBar_MouseDown(self, sender, e):
        try:
            self.DragMove()
        except Exception:
            pass

def get_version():
    try:
        curr = os.path.dirname(__file__)
        for _ in range(5):
            v_file = os.path.join(curr, "version.txt")
            if os.path.exists(v_file):
                with open(v_file, "r") as f:
                    ver = f.read().strip()
                    if ver:
                        return ver
            curr = os.path.dirname(curr)
    except Exception:
        pass
    return "3.0.0"

def get_previous_version():
    try:
        curr = os.path.dirname(__file__)
        for _ in range(5):
            v_file = os.path.join(curr, "prev_version.txt")
            if os.path.exists(v_file):
                with open(v_file, "r") as f:
                    ver = f.read().strip()
                    if ver:
                        return ver
            curr = os.path.dirname(curr)
    except Exception:
        pass
    return "2.5.10"

def show_whats_new(prev_version=None, current_version=None):
    try:
        if not current_version:
            current_version = get_version()
        if not prev_version:
            prev_version = get_previous_version()
            
        cur_disp = "v" + current_version if not current_version.lower().startswith("v") else current_version
        prev_disp = "v" + prev_version if not prev_version.lower().startswith("v") else prev_version
        
        xaml_content = XAML_STRING.replace("{VERSION}", cur_disp).replace("{PREV_VERSION}", prev_disp)
        w = WhatsNewWindow(xaml_content, literal_string=True)
        w.ShowDialog()
    except Exception as e:
        try:
            forms.alert("Could not display What's New window:\n" + str(e), title="What's New")
        except Exception:
            pass

if __name__ == '__main__':
    show_whats_new()
