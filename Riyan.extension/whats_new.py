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
        Title="Riyan Revit Tools - V2.4.0 Release" Height="580" Width="820"
        WindowStartupLocation="CenterScreen"
        Background="Transparent" WindowStyle="None" AllowsTransparency="True"
        ResizeMode="NoResize" FontFamily="Segoe UI">

    <Window.Resources>
        <SolidColorBrush x:Key="WindowBg" Color="#1E1E22"/>
        <SolidColorBrush x:Key="CardBg" Color="#26262B"/>
        <SolidColorBrush x:Key="CardBorder" Color="#383842"/>
        <SolidColorBrush x:Key="PrimaryMaroon" Color="#802F2D"/>
        <SolidColorBrush x:Key="PrimaryHover" Color="#A13B38"/>
        <SolidColorBrush x:Key="EmeraldText" Color="#34D399"/>
        <SolidColorBrush x:Key="EmeraldBg" Color="#152E24"/>
        <SolidColorBrush x:Key="TextWhite" Color="#FFFFFF"/>
        <SolidColorBrush x:Key="TextMuted" Color="#9CA3AF"/>

        <Style x:Key="PrimaryBtn" TargetType="Button">
            <Setter Property="Background" Value="{StaticResource PrimaryMaroon}"/>
            <Setter Property="Foreground" Value="White"/>
            <Setter Property="FontWeight" Value="Bold"/>
            <Setter Property="FontSize" Value="13"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border x:Name="border" Background="{TemplateBinding Background}" CornerRadius="8" Padding="20,10">
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
    </Window.Resources>

    <Border Background="{StaticResource WindowBg}" CornerRadius="12" BorderBrush="#4B5563" BorderThickness="1">
        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="45"/>
                <RowDefinition Height="75"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="65"/>
            </Grid.RowDefinitions>

            <!-- Custom Draggable Title Bar -->
            <Grid x:Name="TitleBar" Grid.Row="0" Background="#161619">
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="40"/>
                </Grid.ColumnDefinitions>
                <StackPanel Orientation="Horizontal" VerticalAlignment="Center" Margin="16,0,0,0">
                    <TextBlock Text="🌟" FontSize="14" Margin="0,0,8,0" VerticalAlignment="Center"/>
                    <TextBlock Text="What's New in Riyan Tools - V2.4.0" Foreground="#D1D5DB" FontSize="12" FontWeight="SemiBold" VerticalAlignment="Center"/>
                </StackPanel>
                <Button x:Name="BtnCloseX" Grid.Column="1" Content="✕" Foreground="#9CA3AF" Background="Transparent" BorderThickness="0" FontSize="14" Cursor="Hand"/>
            </Grid>

            <!-- Header Section -->
            <Border Grid.Row="1" Background="#242429" BorderBrush="#374151" BorderThickness="0,0,0,1" Padding="25,12">
                <Grid>
                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="60"/>
                        <ColumnDefinition Width="*"/>
                        <ColumnDefinition Width="Auto"/>
                    </Grid.ColumnDefinitions>

                    <!-- Icon / Brand Badge -->
                    <Border Grid.Column="0" Width="48" Height="48" CornerRadius="10" Background="{StaticResource PrimaryMaroon}" Margin="0,0,12,0">
                        <TextBlock Text="R" Foreground="White" FontSize="26" FontWeight="Black" HorizontalAlignment="Center" VerticalAlignment="Center"/>
                    </Border>

                    <!-- Title Info -->
                    <StackPanel Grid.Column="1" VerticalAlignment="Center">
                        <StackPanel Orientation="Horizontal">
                            <TextBlock Text="Riyan Revit Tools" Foreground="{StaticResource TextWhite}" FontSize="20" FontWeight="Black" Margin="0,0,10,0"/>
                            <Border Background="{StaticResource EmeraldBg}" BorderBrush="#059669" BorderThickness="1" CornerRadius="12" Padding="8,2" VerticalAlignment="Center">
                                <TextBlock Text="V2.4.0 UPDATE" Foreground="{StaticResource EmeraldText}" FontSize="11" FontWeight="Bold"/>
                            </Border>
                        </StackPanel>
                        <TextBlock Text="Riyan Library Browser, Instant Theme Switching &amp; Zero-Touch Self-Healing" Foreground="{StaticResource TextMuted}" FontSize="12" Margin="0,4,0,3"/>
                        <TextBlock Text="Engineering Team: Asanka, Udarie, Chalana &amp; Dilupa" Foreground="#D1D5DB" FontSize="11" FontWeight="SemiBold"/>
                    </StackPanel>

                    <!-- Status Pill -->
                    <Border Grid.Column="2" Background="#182A20" BorderBrush="#059669" BorderThickness="1" CornerRadius="8" Padding="12,6" VerticalAlignment="Center">
                        <StackPanel Orientation="Horizontal">
                            <TextBlock Text="OK" Foreground="{StaticResource EmeraldText}" FontSize="11" FontWeight="Bold" Margin="0,0,6,0"/>
                            <TextBlock Text="100% Tested &amp; Active" Foreground="{StaticResource EmeraldText}" FontSize="11" FontWeight="Bold"/>
                        </StackPanel>
                    </Border>
                </Grid>
            </Border>

            <!-- Features Grid (4 Cards) -->
            <Grid Grid.Row="2" Margin="25,18,25,10">
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="15"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>
                <Grid.RowDefinitions>
                    <RowDefinition Height="*"/>
                    <RowDefinition Height="15"/>
                    <RowDefinition Height="*"/>
                </Grid.RowDefinitions>

                <!-- Card 1: Riyan Library Browser -->
                <Border Grid.Row="0" Grid.Column="0" Background="{StaticResource CardBg}" BorderBrush="{StaticResource CardBorder}" BorderThickness="1" CornerRadius="10" Padding="14">
                    <Grid>
                        <Grid.ColumnDefinitions>
                            <ColumnDefinition Width="38"/>
                            <ColumnDefinition Width="*"/>
                        </Grid.ColumnDefinitions>
                        <Border Grid.Column="0" Width="28" Height="28" Background="#1E293B" CornerRadius="6" VerticalAlignment="Top" Margin="0,2,0,0">
                            <TextBlock Text="[L]" Foreground="#60A5FA" FontSize="12" FontWeight="Bold" HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                        <StackPanel Grid.Column="1">
                            <StackPanel Orientation="Horizontal">
                                <TextBlock Text="Riyan Library Browser" Foreground="{StaticResource TextWhite}" FontWeight="Bold" FontSize="13" Margin="0,0,6,0"/>
                                <Border Background="#1E293B" CornerRadius="4" Padding="4,1" VerticalAlignment="Center">
                                    <TextBlock Text="2,380+ Families" Foreground="#60A5FA" FontSize="9" FontWeight="Bold"/>
                                </Border>
                            </StackPanel>
                            <TextBlock Text="Instant browsing and 1-click loading of architectural &amp; structural families, System Walls, multi-select bulk loading, master RVT type name sync, and acrylic dark/light theme."
                                       Foreground="{StaticResource TextMuted}" FontSize="11" TextWrapping="Wrap" Margin="0,5,0,0" LineHeight="16"/>
                        </StackPanel>
                    </Grid>
                </Border>

                <!-- Card 2: Instant Theme Switching -->
                <Border Grid.Row="0" Grid.Column="2" Background="{StaticResource CardBg}" BorderBrush="{StaticResource CardBorder}" BorderThickness="1" CornerRadius="10" Padding="14">
                    <Grid>
                        <Grid.ColumnDefinitions>
                            <ColumnDefinition Width="38"/>
                            <ColumnDefinition Width="*"/>
                        </Grid.ColumnDefinitions>
                        <Border Grid.Column="0" Width="28" Height="28" Background="#1E3A2F" CornerRadius="6" VerticalAlignment="Top" Margin="0,2,0,0">
                            <TextBlock Text="[T]" Foreground="{StaticResource EmeraldText}" FontSize="12" FontWeight="Bold" HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                        <StackPanel Grid.Column="1">
                            <StackPanel Orientation="Horizontal">
                                <TextBlock Text="Instant In-Place Theme Switching" Foreground="{StaticResource TextWhite}" FontWeight="Bold" FontSize="13" Margin="0,0,6,0"/>
                                <Border Background="#1E3A2F" CornerRadius="4" Padding="4,1" VerticalAlignment="Center">
                                    <TextBlock Text="Zero-Flicker" Foreground="{StaticResource EmeraldText}" FontSize="9" FontWeight="Bold"/>
                                </Border>
                            </StackPanel>
                            <TextBlock Text="Universal smooth instant theme toggle (Dark &amp; Light) across Export Manager, Batch Export, and Library with zero window reloading, zero lag, and zero disappearance."
                                       Foreground="{StaticResource TextMuted}" FontSize="11" TextWrapping="Wrap" Margin="0,5,0,0" LineHeight="16"/>
                        </StackPanel>
                    </Grid>
                </Border>

                <!-- Card 3: Light Theme Polish & Typography -->
                <Border Grid.Row="2" Grid.Column="0" Background="{StaticResource CardBg}" BorderBrush="{StaticResource CardBorder}" BorderThickness="1" CornerRadius="10" Padding="14">
                    <Grid>
                        <Grid.ColumnDefinitions>
                            <ColumnDefinition Width="38"/>
                            <ColumnDefinition Width="*"/>
                        </Grid.ColumnDefinitions>
                        <Border Grid.Column="0" Width="28" Height="28" Background="#311F3B" CornerRadius="6" verticalAlignment="Top" Margin="0,2,0,0">
                            <TextBlock Text="[P]" Foreground="#C084FC" FontSize="12" FontWeight="Bold" HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                        <StackPanel Grid.Column="1">
                            <StackPanel Orientation="Horizontal">
                                <TextBlock Text="Refined Light Theme Polish" Foreground="{StaticResource TextWhite}" FontWeight="Bold" FontSize="13" Margin="0,0,6,0"/>
                                <Border Background="#311F3B" CornerRadius="4" Padding="4,1" VerticalAlignment="Center">
                                    <TextBlock Text="High Contrast" Foreground="#C084FC" FontSize="9" FontWeight="Bold"/>
                                </Border>
                            </StackPanel>
                            <TextBlock Text="Complete Light Theme visual overhaul with crisp white cards, clean light-gray headers, warm readable amber file accents, soft row highlights, and perfect typography contrast."
                                       Foreground="{StaticResource TextMuted}" FontSize="11" TextWrapping="Wrap" Margin="0,5,0,0" LineHeight="16"/>
                        </StackPanel>
                    </Grid>
                </Border>

                <!-- Card 4: Zero-Touch Startup Self-Healing -->
                <Border Grid.Row="2" Grid.Column="2" Background="{StaticResource CardBg}" BorderBrush="{StaticResource CardBorder}" BorderThickness="1" CornerRadius="10" Padding="14">
                    <Grid>
                        <Grid.ColumnDefinitions>
                            <ColumnDefinition Width="38"/>
                            <ColumnDefinition Width="*"/>
                        </Grid.ColumnDefinitions>
                        <Border Grid.Column="0" Width="28" Height="28" Background="#3B311B" CornerRadius="6" VerticalAlignment="Top" Margin="0,2,0,0">
                            <TextBlock Text="[S]" Foreground="#FBBF24" FontSize="12" FontWeight="Bold" HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                        <StackPanel Grid.Column="1">
                            <StackPanel Orientation="Horizontal">
                                <TextBlock Text="Zero-Touch Startup Self-Healing" Foreground="{StaticResource TextWhite}" FontWeight="Bold" FontSize="13" Margin="0,0,6,0"/>
                                <Border Background="#3B311B" CornerRadius="4" Padding="4,1" VerticalAlignment="Center">
                                    <TextBlock Text="Multi-PC Sync" Foreground="#FBBF24" FontSize="9" FontWeight="Bold"/>
                                </Border>
                            </StackPanel>
                            <TextBlock Text="Automatic background startup routine in startup.py silently purges orphan button caches and pyRevit UI artifacts on Revit launch across all office workstations."
                                       Foreground="{StaticResource TextMuted}" FontSize="11" TextWrapping="Wrap" Margin="0,5,0,0" LineHeight="16"/>
                        </StackPanel>
                    </Grid>
                </Border>
            </Grid>

            <!-- Footer Bar -->
            <Border Grid.Row="3" Background="#161619" CornerRadius="0,0,12,12" Padding="25,0">
                <Grid>
                    <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                        <TextBlock Text="Production Engine: " Foreground="{StaticResource TextMuted}" FontSize="12"/>
                        <TextBlock Text="Revit 2022-2026 Active Production | 2027+ Ready" Foreground="{StaticResource EmeraldText}" FontSize="12" FontWeight="Bold"/>
                    </StackPanel>
                    <Button x:Name="BtnGotIt" Content="Got It, Let's Work!" Style="{StaticResource PrimaryBtn}" HorizontalAlignment="Right" VerticalAlignment="Center"/>
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
            
    def CloseBtn_Click(self, sender, e):
        self.Close()
        
    def TitleBar_MouseDown(self, sender, e):
        try:
            self.DragMove()
        except Exception:
            pass

def show_whats_new():
    try:
        w = WhatsNewWindow(XAML_STRING, literal_string=True)
        w.ShowDialog()
    except Exception as e:
        try:
            forms.alert("Could not display What's New window:\n" + str(e), title="What's New")
        except Exception:
            pass

if __name__ == '__main__':
    show_whats_new()


