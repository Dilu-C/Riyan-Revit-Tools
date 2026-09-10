# -*- coding: utf-8 -*-
import os
import sys
import clr
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')
clr.AddReference('System.Xaml')

import System
from System.Windows.Markup import XamlReader
from System.Windows import Application, Window

XAML_STRING = """
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Riyan Revit Tools - V2.2 Release" Height="580" Width="820"
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
        <SolidColorBrush x:Key="TextWhite" Color="#F3F4F6"/>
        <SolidColorBrush x:Key="TextMuted" Color="#9CA3AF"/>
        
        <Style x:Key="PrimaryBtn" TargetType="Button">
            <Setter Property="Background" Value="{StaticResource PrimaryMaroon}"/>
            <Setter Property="Foreground" Value="White"/>
            <Setter Property="BorderThickness" Value="0"/>
            <Setter Property="Padding" Value="24,8"/>
            <Setter Property="FontSize" Value="13"/>
            <Setter Property="FontWeight" Value="Bold"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border x:Name="bd" Background="{TemplateBinding Background}" CornerRadius="8">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter TargetName="bd" Property="Background" Value="{StaticResource PrimaryHover}"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>
    </Window.Resources>

    <Border Background="{StaticResource WindowBg}" CornerRadius="14" BorderBrush="{StaticResource PrimaryMaroon}" BorderThickness="2">
        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="45"/>
                <RowDefinition Height="Auto"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="65"/>
            </Grid.RowDefinitions>

            <!-- Title Bar -->
            <Border x:Name="TitleBar" Grid.Row="0" Background="#161619" CornerRadius="12,12,0,0" Padding="18,0,10,0">
                <Grid>
                    <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                        <TextBlock Text="Riyan BIM Automation System" Foreground="{StaticResource TextMuted}" FontSize="12" FontWeight="SemiBold"/>
                    </StackPanel>
                    <Button x:Name="BtnClose" Content="✕" Width="36" Height="32" Background="Transparent" Foreground="{StaticResource TextMuted}" 
                            BorderThickness="0" FontSize="14" Cursor="Hand" HorizontalAlignment="Right" VerticalAlignment="Center"/>
                </Grid>
            </Border>

            <!-- Header Section -->
            <Border Grid.Row="1" Padding="25,20,25,15" BorderBrush="#2D2D35" BorderThickness="0,0,0,1">
                <Grid>
                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="Auto"/>
                        <ColumnDefinition Width="*"/>
                        <ColumnDefinition Width="Auto"/>
                    </Grid.ColumnDefinitions>

                    <!-- Logo Box -->
                    <Border Grid.Column="0" Width="48" Height="48" CornerRadius="12" Background="{StaticResource PrimaryMaroon}" Margin="0,0,16,0">
                        <TextBlock Text="R" Foreground="White" FontSize="26" FontWeight="Black" HorizontalAlignment="Center" VerticalAlignment="Center"/>
                    </Border>

                    <!-- Title Info -->
                    <StackPanel Grid.Column="1" VerticalAlignment="Center">
                        <StackPanel Orientation="Horizontal">
                            <TextBlock Text="Riyan Revit Tools" Foreground="{StaticResource TextWhite}" FontSize="20" FontWeight="Black" Margin="0,0,10,0"/>
                            <Border Background="{StaticResource EmeraldBg}" BorderBrush="#059669" BorderThickness="1" CornerRadius="12" Padding="8,2" VerticalAlignment="Center">
                                <TextBlock Text="V2.2 UPDATE" Foreground="{StaticResource EmeraldText}" FontSize="11" FontWeight="Bold"/>
                            </Border>
                        </StackPanel>
                        <TextBlock Text="Full-Cell Selection, Spacebar Multi-Toggle &amp; Instant Dialog Shortcuts" Foreground="{StaticResource TextMuted}" FontSize="12" Margin="0,4,0,3"/>
                        <TextBlock Text="👨‍💻 Engineering Team: Asanka, Udarie, Chalana &amp; Dilupa" Foreground="#D1D5DB" FontSize="11" FontWeight="SemiBold"/>
                    </StackPanel>

                    <!-- Status Pill -->
                    <Border Grid.Column="2" Background="#182A20" BorderBrush="#059669" BorderThickness="1" CornerRadius="8" Padding="12,6" VerticalAlignment="Center">
                        <StackPanel Orientation="Horizontal">
                            <TextBlock Text="●" Foreground="{StaticResource EmeraldText}" FontSize="12" Margin="0,0,6,0"/>
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

                <!-- Card 1: Full-Cell Sheet Selection -->
                <Border Grid.Row="0" Grid.Column="0" Background="{StaticResource CardBg}" BorderBrush="{StaticResource CardBorder}" BorderThickness="1" CornerRadius="10" Padding="14">
                    <Grid>
                        <Grid.ColumnDefinitions>
                            <ColumnDefinition Width="38"/>
                            <ColumnDefinition Width="*"/>
                        </Grid.ColumnDefinitions>
                        <TextBlock Grid.Column="0" Text="🎯" FontSize="22" VerticalAlignment="Top" Margin="0,2,0,0"/>
                        <StackPanel Grid.Column="1">
                            <StackPanel Orientation="Horizontal">
                                <TextBlock Text="Full-Cell Click Selection" Foreground="{StaticResource TextWhite}" FontWeight="Bold" FontSize="13" Margin="0,0,6,0"/>
                                <Border Background="#1E3A2F" CornerRadius="4" Padding="4,1" VerticalAlignment="Center">
                                    <TextBlock Text="Edge-to-Edge" Foreground="{StaticResource EmeraldText}" FontSize="9" FontWeight="Bold"/>
                                </Border>
                            </StackPanel>
                            <TextBlock Text="No need to hit the tiny checkbox! Click anywhere across the entire cell or header to toggle sheet selection immediately with instant Hand feedback."
                                       Foreground="{StaticResource TextMuted}" FontSize="11" TextWrapping="Wrap" Margin="0,5,0,0" LineHeight="16"/>
                        </StackPanel>
                    </Grid>
                </Border>

                <!-- Card 2: Spacebar Multi-Select -->
                <Border Grid.Row="0" Grid.Column="2" Background="{StaticResource CardBg}" BorderBrush="{StaticResource CardBorder}" BorderThickness="1" CornerRadius="10" Padding="14">
                    <Grid>
                        <Grid.ColumnDefinitions>
                            <ColumnDefinition Width="38"/>
                            <ColumnDefinition Width="*"/>
                        </Grid.ColumnDefinitions>
                        <TextBlock Grid.Column="0" Text="⌨️" FontSize="22" VerticalAlignment="Top" Margin="0,2,0,0"/>
                        <StackPanel Grid.Column="1">
                            <StackPanel Orientation="Horizontal">
                                <TextBlock Text="Spacebar Multi-Row Toggle" Foreground="{StaticResource TextWhite}" FontWeight="Bold" FontSize="13" Margin="0,0,6,0"/>
                                <Border Background="#3B311B" CornerRadius="4" Padding="4,1" VerticalAlignment="Center">
                                    <TextBlock Text="Rapid Workflow" Foreground="#FBBF24" FontSize="9" FontWeight="Bold"/>
                                </Border>
                            </StackPanel>
                            <TextBlock Text="Select multiple sheet rows with Shift/Ctrl click, then press Spacebar or click any selected checkbox to toggle all of them simultaneously."
                                       Foreground="{StaticResource TextMuted}" FontSize="11" TextWrapping="Wrap" Margin="0,5,0,0" LineHeight="16"/>
                        </StackPanel>
                    </Grid>
                </Border>

                <!-- Card 3: Rapid Dialog Shortcuts -->
                <Border Grid.Row="2" Grid.Column="0" Background="{StaticResource CardBg}" BorderBrush="{StaticResource CardBorder}" BorderThickness="1" CornerRadius="10" Padding="14">
                    <Grid>
                        <Grid.ColumnDefinitions>
                            <ColumnDefinition Width="38"/>
                            <ColumnDefinition Width="*"/>
                        </Grid.ColumnDefinitions>
                        <TextBlock Grid.Column="0" Text="⚡" FontSize="22" VerticalAlignment="Top" Margin="0,2,0,0"/>
                        <StackPanel Grid.Column="1">
                            <StackPanel Orientation="Horizontal">
                                <TextBlock Text="Enter &amp; Escape Keyboard Control" Foreground="{StaticResource TextWhite}" FontWeight="Bold" FontSize="13" Margin="0,0,6,0"/>
                                <Border Background="#1E293B" CornerRadius="4" Padding="4,1" VerticalAlignment="Center">
                                    <TextBlock Text="Instant Action" Foreground="#60A5FA" FontSize="9" FontWeight="Bold"/>
                                </Border>
                            </StackPanel>
                            <TextBlock Text="Custom alerts, naming prompts, profile saves, and export completed dialogs now respond immediately to Enter (OK) and Escape (Cancel)."
                                       Foreground="{StaticResource TextMuted}" FontSize="11" TextWrapping="Wrap" Margin="0,5,0,0" LineHeight="16"/>
                        </StackPanel>
                    </Grid>
                </Border>

                <!-- Card 4: Memory Shield & Archiving -->
                <Border Grid.Row="2" Grid.Column="2" Background="{StaticResource CardBg}" BorderBrush="{StaticResource CardBorder}" BorderThickness="1" CornerRadius="10" Padding="14">
                    <Grid>
                        <Grid.ColumnDefinitions>
                            <ColumnDefinition Width="38"/>
                            <ColumnDefinition Width="*"/>
                        </Grid.ColumnDefinitions>
                        <TextBlock Grid.Column="0" Text="🛡️" FontSize="22" VerticalAlignment="Top" Margin="0,2,0,0"/>
                        <StackPanel Grid.Column="1">
                            <StackPanel Orientation="Horizontal">
                                <TextBlock Text="Zero-Hang Memory Shield" Foreground="{StaticResource TextWhite}" FontWeight="Bold" FontSize="13" Margin="0,0,6,0"/>
                                <Border Background="#311F3B" CornerRadius="4" Padding="4,1" VerticalAlignment="Center">
                                    <TextBlock Text="Rock Solid" Foreground="#C084FC" FontSize="9" FontWeight="Bold"/>
                                </Border>
                            </StackPanel>
                            <TextBlock Text="Smart selective archiving and robust background model release ensure zero lingering handles and lightning-fast Revit operation."
                                       Foreground="{StaticResource TextMuted}" FontSize="11" TextWrapping="Wrap" Margin="0,5,0,0" LineHeight="16"/>
                        </StackPanel>
                    </Grid>
                </Border>
            </Grid>

            <!-- Footer Bar -->
            <Border Grid.Row="3" Background="#161619" CornerRadius="0,0,12,12" Padding="25,0">
                <Grid>
                    <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                        <TextBlock Text="⚡ Production Engine: " Foreground="{StaticResource TextMuted}" FontSize="12"/>
                        <TextBlock Text="Revit 2022–2026 Active Production | 2027+ Ready" Foreground="{StaticResource EmeraldText}" FontSize="12" FontWeight="Bold"/>
                    </StackPanel>
                    <Button x:Name="BtnGotIt" Content="Got It, Let's Work! 🚀" Style="{StaticResource PrimaryBtn}" HorizontalAlignment="Right" VerticalAlignment="Center"/>
                </Grid>
            </Border>
        </Grid>
    </Border>
</Window>
"""

def show_whats_new():
    try:
        def _open():
            win = XamlReader.Parse(XAML_STRING)
            
            btn_close = win.FindName("BtnClose")
            btn_close.Click += lambda s, e: win.Close()
            
            btn_got_it = win.FindName("BtnGotIt")
            btn_got_it.Click += lambda s, e: win.Close()
            
            title_bar = win.FindName("TitleBar")
            def on_drag(s, e):
                try: win.DragMove()
                except: pass
            title_bar.MouseLeftButtonDown += on_drag
            
            win.ShowDialog()

        if Application.Current and Application.Current.Dispatcher and not Application.Current.Dispatcher.CheckAccess():
            Application.Current.Dispatcher.Invoke(System.Action(_open))
        else:
            _open()
    except Exception as e:
        try:
            from pyrevit import forms
            forms.alert("Could not display What's New window:\n" + str(e), title="What's New")
        except:
            pass

if __name__ == '__main__':
    show_whats_new()

