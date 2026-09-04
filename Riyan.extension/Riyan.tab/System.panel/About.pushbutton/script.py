# -*- coding: utf-8 -*-
import os
import System
from pyrevit import forms
from System.Windows.Markup import XamlReader
from System.Windows.Media.Imaging import BitmapImage
from System import Uri, UriKind
import clr
clr.AddReference("System")

def get_version():
    try:
        curr = os.path.dirname(__file__)
        for _ in range(5):
            v_file = os.path.join(curr, "version.txt")
            if os.path.exists(v_file):
                with open(v_file, "r") as f:
                    return f.read().strip()
            curr = os.path.dirname(curr)
    except:
        pass
    return "1.3"

VERSION = get_version()

def show_about_dialog():
    plugin_dir = os.path.dirname(__file__)
    logo_path = os.path.join(plugin_dir, "logo.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(plugin_dir, "icon.png")

    xaml_str = """
    <Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
            xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
            Title="About Riyan Plugin" Height="290" Width="400"
            WindowStartupLocation="CenterScreen"
            Background="Transparent" WindowStyle="None" AllowsTransparency="True"
            ResizeMode="NoResize" FontFamily="Segoe UI">

        <Window.Resources>
            <Style x:Key="PrimaryBtn" TargetType="Button">
                <Setter Property="Background"       Value="#802F2D"/>
                <Setter Property="Foreground"       Value="White"/>
                <Setter Property="BorderThickness"  Value="0"/>
                <Setter Property="Padding"          Value="0"/>
                <Setter Property="FontSize"         Value="12"/>
                <Setter Property="FontWeight"       Value="SemiBold"/>
                <Setter Property="Cursor"           Value="Hand"/>
                <Setter Property="Height"           Value="32"/>
                <Setter Property="Template">
                    <Setter.Value>
                        <ControlTemplate TargetType="Button">
                            <Border x:Name="bd" Background="{TemplateBinding Background}" CornerRadius="6">
                                <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                            </Border>
                            <ControlTemplate.Triggers>
                                <Trigger Property="IsMouseOver" Value="True">
                                    <Setter TargetName="bd" Property="Background" Value="#9E3A38"/>
                                </Trigger>
                                <Trigger Property="IsPressed" Value="True">
                                    <Setter TargetName="bd" Property="Background" Value="#661F1D"/>
                                </Trigger>
                            </ControlTemplate.Triggers>
                        </ControlTemplate>
                    </Setter.Value>
                </Setter>
            </Style>
        </Window.Resources>

        <Border Background="#F3F4F6" CornerRadius="10" BorderBrush="#D1D5DB" BorderThickness="1">
            <Border.Effect>
                <DropShadowEffect Color="Black" Opacity="0.1" BlurRadius="10" ShadowDepth="2"/>
            </Border.Effect>
            <Grid>
                <Grid.RowDefinitions>
                    <RowDefinition Height="36"/>
                    <RowDefinition Height="*"/>
                </Grid.RowDefinitions>
                
                <!-- TITLE BAR -->
                <Border x:Name="TitleBarBorder" Grid.Row="0" Background="#E5E7EB" CornerRadius="10,10,0,0" BorderBrush="#D1D5DB" BorderThickness="0,0,0,1">
                    <Grid>
                        <StackPanel Orientation="Horizontal" VerticalAlignment="Center" Margin="15,0,0,0">
                            <TextBlock Text="About Riyan" Foreground="#802F2D" FontSize="13" FontWeight="Bold" VerticalAlignment="Center"/>
                        </StackPanel>
                        
                        <StackPanel Orientation="Horizontal" HorizontalAlignment="Right" VerticalAlignment="Top">
                            <Button x:Name="CloseBtn" Content="✕" Width="36" Height="35" BorderThickness="0" Cursor="Hand" Background="Transparent" Foreground="#6B7280" FontSize="11" FontWeight="Bold">
                                <Button.Style>
                                    <Style TargetType="Button">
                                        <Setter Property="Template">
                                            <Setter.Value>
                                                <ControlTemplate TargetType="Button">
                                                    <Border x:Name="bd" Background="{TemplateBinding Background}" CornerRadius="0,9,0,0">
                                                        <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                                                    </Border>
                                                    <ControlTemplate.Triggers>
                                                        <Trigger Property="IsMouseOver" Value="True">
                                                            <Setter TargetName="bd" Property="Background" Value="#802F2D"/>
                                                            <Setter Property="Foreground" Value="#FFFFFF"/>
                                                        </Trigger>
                                                        <Trigger Property="IsPressed" Value="True">
                                                            <Setter TargetName="bd" Property="Background" Value="#661F1D"/>
                                                            <Setter Property="Foreground" Value="#FFFFFF"/>
                                                        </Trigger>
                                                    </ControlTemplate.Triggers>
                                                </ControlTemplate>
                                            </Setter.Value>
                                        </Setter>
                                    </Style>
                                </Button.Style>
                            </Button>
                        </StackPanel>
                    </Grid>
                </Border>

                <!-- CONTENT -->
                <Grid Grid.Row="1" Margin="25,20,25,20">
                    <Grid.RowDefinitions>
                        <RowDefinition Height="Auto"/>
                        <RowDefinition Height="Auto"/>
                        <RowDefinition Height="Auto"/>
                        <RowDefinition Height="*"/>
                    </Grid.RowDefinitions>
                    
                    <Image x:Name="BigLogo" Height="40" Margin="0,0,0,15" RenderOptions.BitmapScalingMode="HighQuality" HorizontalAlignment="Center" Grid.Row="0"/>
                    
                    <TextBlock Text="Riyan Revit Plugin Suite" FontSize="18" FontWeight="Bold" Foreground="#111827" HorizontalAlignment="Center" Margin="0,0,0,5" Grid.Row="1"/>
                    
                    <StackPanel Grid.Row="2" Margin="0,15,0,15">
                        <Grid Margin="0,0,0,10">
                            <TextBlock Text="Version" Foreground="#6B7280" HorizontalAlignment="Left" FontSize="13" FontWeight="SemiBold"/>
                            <TextBlock Text="V{version}" Foreground="#111827" FontWeight="Bold" HorizontalAlignment="Right" FontSize="13"/>
                        </Grid>
                        <Grid>
                            <TextBlock Text="Developer" Foreground="#6B7280" HorizontalAlignment="Left" FontSize="13" FontWeight="SemiBold"/>
                            <TextBlock Text="Asanka, Udarie, Chalana &amp; Dilupa" Foreground="#111827" FontWeight="Bold" HorizontalAlignment="Right" FontSize="13"/>
                        </Grid>
                    </StackPanel>

                    <Button x:Name="BtnOk" Content="OK" Width="100" Style="{StaticResource PrimaryBtn}" HorizontalAlignment="Center" VerticalAlignment="Bottom" Grid.Row="3"/>
                </Grid>
            </Grid>
        </Border>
    </Window>
    """.replace("{version}", VERSION)

    window = XamlReader.Parse(xaml_str)
    
    logo_img = window.FindName("BigLogo")
    if os.path.exists(logo_path):
        uri = Uri(logo_path, UriKind.Absolute)
        logo_img.Source = BitmapImage(uri)
    
    close_btn = window.FindName("CloseBtn")
    close_btn.Click += lambda s, e: window.Close()
    
    btn_ok = window.FindName("BtnOk")
    btn_ok.Click += lambda s, e: window.Close()
    
    def title_bar_drag(sender, e):
        try: window.DragMove()
        except: pass
        
    border_title = window.FindName("TitleBarBorder")
    border_title.MouseLeftButtonDown += title_bar_drag

    window.ShowDialog()

if __name__ == '__main__':
    show_about_dialog()
