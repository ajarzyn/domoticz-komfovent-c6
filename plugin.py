# DOMEKT air supply plugin
"""
<plugin key="DOMEKT" name="Domekt" author="ajarzyn" version="1.0.1" wikilink="" externallink="">
    <description>
        <h2>Ventia Komfovent C6 Rotatory heat exchanger</h2><br/>
        This plugin allows to control and monitor work parameters of Ventia's Rotatory heat exchangers.
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Monitor work parameters</li>
            <li>Manage temperatures and modes</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Eco Mode - turn eco mode on/off</li>
            <li>Auto Mode - turn Auto mode on/off</li>
            <li>Change current working mode</li>
        </ul>
        <h3>Configuration</h3>
        Set correct IP address for your ventilation central.
        If you do not know IP it is good guess that default will fit.
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="30px" required="true" default="502"/>
        <param field="Mode5" label="SyncTime" width="75px">
            <options>
                <option label="True" value="true"/>
                <option label="False" value="false"  default="true" />
            </options>
        </param>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="true"/>
                <option label="False" value="false"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import ctypes
import datetime

from pymodbus.constants import Endian
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder


class BasePlugin:
    enabled = False
    debug = False
    available_mode_levels = [10, 20, 30, 40]

    UNITS = {
        'ECO':  1,
        'Auto': 2,
        'Temp': 3,
        'Hum':  4,
        'Mode': 5,
        'OutdoorTemp': 6,
        'SupplyTemp': 7,
        'ExtractTemp': 8,
        'WaterTemp': 9,
        'TotalEnergyConsumtion': 11,
        'TotalHeaterConsumtion': 12,
        'TotalEnergyRecovered': 13,
        'CurrentExchangeEfficiency': 14,
        'CurrentEnergySaving': 15,

        'SupplyFanIntensivity': 20,
        'ExtractFanIntensivity': 21,
        'HeatExchanger': 22,
        'ElectricHeater': 23,
        'WaterHeater': 24,
        'WaterCooler': 25,
        'DXUnit': 26,
        'FiltersImupurity': 27,

        'TempControlType': 50,
        'OnOff': 51,
        'Kitchen': 52,
        'Fireplace': 53
        }

    def __init__(self):
        self.sync_time = False
        return

    def onStart(self):
        # setup the appropriate logging level
        if Parameters['Mode5'] == "true":
            self.sync_time = True
        if Parameters['Mode6'] == "true":
            Domoticz.Debugging(1)
            DumpConfigToLog()
            self.debug = True
        else:
            Domoticz.Debugging(0)

        self.client = ModbusTcpClient(Parameters['Address'], port=int(Parameters['Port']))

        if self.UNITS['OnOff'] not in Devices:
            Domoticz.Device(Name="OnOff", Unit=self.UNITS['OnOff'], TypeName="Switch", Image=9, Used=1).Create()
        if self.UNITS['ECO'] not in Devices:
            Domoticz.Device(Name="ECO", Unit=self.UNITS['ECO'], TypeName="Switch", Image=9, Used=1).Create()
        if self.UNITS['Auto'] not in Devices:
            Domoticz.Device(Name="Auto", Unit=self.UNITS['Auto'], TypeName="Switch", Image=9, Used=1).Create()
        if self.UNITS['Temp'] not in Devices:
            Domoticz.Device(Name="Panel1 Temperature", Unit=self.UNITS['Temp'], TypeName="Temperature", Used=1).Create()
        if self.UNITS['Hum'] not in Devices:
            Domoticz.Device(Name="Panel1 Humidity", Unit=self.UNITS['Hum'], TypeName="Humidity", Used=1).Create()
        if self.UNITS['Mode'] not in Devices:
            Options = {"LevelActions": "||||||||||",
                       "LevelNames": "Standby|Away|Normal|Intensive|Boost|Kitchen|Fireplace|Ovveride|Holiday|AirQuality|Off",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
            Domoticz.Device(Name="Mode", Unit=self.UNITS['Mode'], TypeName="Selector Switch", Used=1, Image=7,
                            Options=Options).Create()

        if self.UNITS['OutdoorTemp'] not in Devices:
            Domoticz.Device(Name="Outside Temperature", Unit=self.UNITS['OutdoorTemp'],
                            TypeName="Temperature", Used=1).Create()
        if self.UNITS['SupplyTemp'] not in Devices:
            Domoticz.Device(Name="Air Blowed In Temperature", Unit=self.UNITS['SupplyTemp'],
                            TypeName="Temperature", Used=1).Create()
        if self.UNITS['ExtractTemp'] not in Devices:
            Domoticz.Device(Name="Air Blowed Out Temperature", Unit=self.UNITS['ExtractTemp'],
                            TypeName="Temperature", Used=1).Create()
        if self.UNITS['WaterTemp'] not in Devices:
            Domoticz.Device(Name="Water Temperature", Unit=self.UNITS['WaterTemp'],
                            TypeName="Temperature", Used=1).Create()

        if self.UNITS['SupplyFanIntensivity'] not in Devices:
            Domoticz.Device(Name="Supply Fan Intensivity", Unit=self.UNITS['SupplyFanIntensivity'],
                            TypeName="Percentage", Used=1).Create()
        if self.UNITS['ExtractFanIntensivity'] not in Devices:
            Domoticz.Device(Name="Extract Fan Intensivity", Unit=self.UNITS['ExtractFanIntensivity'],
                            TypeName="Percentage", Used=1).Create()
        if self.UNITS['HeatExchanger'] not in Devices:
            Domoticz.Device(Name="Heat Exchanger", Unit=self.UNITS['HeatExchanger'],
                            TypeName="Percentage", Used=1).Create()
        if self.UNITS['ElectricHeater'] not in Devices:
            Domoticz.Device(Name="Electric Heater", Unit=self.UNITS['ElectricHeater'],
                            TypeName="Percentage", Used=1).Create()
        if self.UNITS['WaterHeater'] not in Devices:
            Domoticz.Device(Name="Water Heater", Unit=self.UNITS['WaterHeater'],
                            TypeName="Percentage", Used=1).Create()
        if self.UNITS['WaterCooler'] not in Devices:
            Domoticz.Device(Name="Water Cooler", Unit=self.UNITS['WaterCooler'],
                            TypeName="Percentage", Used=1).Create()
        if self.UNITS['DXUnit'] not in Devices:
            Domoticz.Device(Name="DX Unit", Unit=self.UNITS['DXUnit'],
                            TypeName="Percentage", Used=1).Create()
        if self.UNITS['FiltersImupurity'] not in Devices:
            Domoticz.Device(Name="Filters Imupurity", Unit=self.UNITS['FiltersImupurity'],
                            TypeName="Percentage", Used=1).Create()

        if self.UNITS['CurrentEnergySaving'] not in Devices:
            Domoticz.Device(Name="Current Energy Saving", Unit=self.UNITS['CurrentEnergySaving'],
                            TypeName="Percentage", Used=1).Create()
        if self.UNITS['CurrentExchangeEfficiency'] not in Devices:
            Domoticz.Device(Name="Current Exchange Efficiency", Unit=self.UNITS['CurrentExchangeEfficiency'],
                            TypeName="Percentage", Used=1).Create()
        if self.UNITS['TotalEnergyConsumtion'] not in Devices:
            Domoticz.Device(Name="Total Power Consumption", Unit=self.UNITS['TotalEnergyConsumtion'],
                            TypeName="kWh", Used=1).Create()
        if self.UNITS['TotalHeaterConsumtion'] not in Devices:
            Domoticz.Device(Name="Total Heater Consumption", Unit=self.UNITS['TotalHeaterConsumtion'],
                            TypeName="kWh", Used=1).Create()
        if self.UNITS['TotalEnergyRecovered'] not in Devices:
            Domoticz.Device(Name="Total Energy Recovered", Unit=self.UNITS['TotalEnergyRecovered'],
                            TypeName="kWh", Used=1).Create()

        if self.UNITS['TempControlType'] not in Devices:
            Options = {"LevelActions": "||||",
                       "LevelNames": "Off|Supply|Extract|Room|Balance",
                       "LevelOffHidden": "true",
                       "SelectorStyle": "1"}
            Domoticz.Device(Name="TempControlType", Unit=self.UNITS['TempControlType'], TypeName="Selector Switch", Used=1, Image=7,
                            Options=Options).Create()

        if self.UNITS['Kitchen'] not in Devices:
            Domoticz.Device(Name="Kitchen", Unit=self.UNITS['Kitchen'], TypeName="Dimmer", Used=1).Create()
        if self.UNITS['Fireplace'] not in Devices:
            Domoticz.Device(Name="Fireplace", Unit=self.UNITS['Fireplace'], TypeName="Dimmer", Used=1).Create()

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " +
                     str(Level) + str(Hue))
        self.client.connect()

        if Command == 'Set Level':
            if Unit == self.UNITS['Mode']:
                if Level in self.available_mode_levels:
                    self.client.write_register(4, value=int(Level/10))
                    UpdateDevice(Unit, Level, Level, 0)
                    Domoticz.Log("Air flow mode changed.")
                else:
                    Domoticz.Log("Impossible to choose this mode.")

            elif Unit == self.UNITS['TempControlType']:
                if Level in self.available_mode_levels:
                    self.client.write_register(10, value=int((Level-10)/10))
                    UpdateDevice(Unit, Level, Level, 0)
                    Domoticz.Log("Temperature Flow Control mode changed." +str(int((Level-10)/10)))
                else:
                    Domoticz.Log("Impossible to choose this Temperature Flow Control mode.")

            elif Unit == self.UNITS['Kitchen']:
                self.client.write_register(5130, Level)
                UpdateDevice(Unit, Level, Level, 0)

            elif Unit == self.UNITS['Fireplace']:
                self.client.write_register(5137, Level)
                UpdateDevice(Unit, Level, Level, 0)

            self.client.close()
            return

        if Command == 'Off':
            nVal = 0
        elif Command == 'On':
            nVal = 1

        if Unit == self.UNITS['OnOff']:
            rAddr = 0
        elif Unit == self.UNITS['ECO']:
            rAddr = 2
        elif Unit == self.UNITS['Auto']:
            rAddr = 3

        self.client.write_register(rAddr, value=nVal)
        UpdateDevice(Unit, nVal, Command, 0)
        self.client.close()

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        self.client.connect()

        result = self.client.read_holding_registers(0, 11)
        if not result.isError():
            on_off = int(result.registers[0])
            eco = int(result.registers[2])
            auto = int(result.registers[3])
            mode = int(result.registers[4]) * 10
            temp_control = int(result.registers[10]) * 10 + 10

            UpdateDevice(self.UNITS['OnOff'], on_off, str(on_off), 0)
            UpdateDevice(self.UNITS['ECO'], eco, str(eco), 0)
            UpdateDevice(self.UNITS['Auto'], auto,  str(auto), 0)
            UpdateDevice(self.UNITS['Mode'], mode, str(mode), 0)
            if mode == 50:  # Kitchen
                UpdateDevice(self.UNITS['Kitchen'], 5, str(5), 0)
            elif mode == 60:  # Fireplace
                UpdateDevice(self.UNITS['Fireplace'], 5, str(5), 0)
            else:
                UpdateDevice(self.UNITS['Kitchen'], 0, str(0), 0)
                UpdateDevice(self.UNITS['Fireplace'], 0, str(0), 0)

            UpdateDevice(self.UNITS['TempControlType'], temp_control, str(temp_control), 0)

        if self.sync_time:
            result = self.client.read_holding_registers(28, 3)
            if not result.isError():
                time = int(result.registers[0])
                hour, min = time >> 8, time & 0x00FF
                year = int(result.registers[1])
                date = int(result.registers[2])
                month, day = date >> 8, date & 0x00FF

                d1 = datetime.datetime.now()
                if d1.hour != hour or d1.minute != min:
                    time = d1.hour << 8 | d1.minute & 0x00FF
                    self.client.write_register(28, value=time)

                if d1.year != year:
                    self.client.write_register(29, value=year)

                if d1.month != month or d1.day != day:
                    date = d1.month << 8 | d1.day & 0x00FF
                    self.client.write_register(30, value=date)

        registersStartingOffset = 20
        MonitoringDataResult = self.client.read_holding_registers(900, 47)

        if not MonitoringDataResult.isError():
            SupplyTemp  = ConvertToFloat(MonitoringDataResult, 1)
            ExtractTemp = ConvertToFloat(MonitoringDataResult, 2)
            OutdoorTemp = ConvertToFloat(MonitoringDataResult, 3)
            WaterTemp   = ConvertToFloat(MonitoringDataResult, 4)

            UpdateDevice(self.UNITS['OutdoorTemp'], 0, str(OutdoorTemp), 0)
            UpdateDevice(self.UNITS['SupplyTemp'], 0, str(SupplyTemp), 0)
            UpdateDevice(self.UNITS['ExtractTemp'], 0, str(ExtractTemp), 0)
            UpdateDevice(self.UNITS['WaterTemp'], 0, str(WaterTemp), 0)

            SupplyFanIntens     = ConvertToFloat(MonitoringDataResult, 9)
            ExtractFanIntens    = ConvertToFloat(MonitoringDataResult, 10)
            HeatExchanger       = ConvertToFloat(MonitoringDataResult, 11)
            ElectricHeater      = ConvertToFloat(MonitoringDataResult, 12)
            WaterHeater         = ConvertToFloat(MonitoringDataResult, 13)
            WaterCooling        = ConvertToFloat(MonitoringDataResult, 14)
            DXUnit              = ConvertToFloat(MonitoringDataResult, 15)
            FiltersImupurity    = float(MonitoringDataResult.registers[16])

            UpdateDevice(self.UNITS['SupplyFanIntensivity'], 0, str(SupplyFanIntens), 0)
            UpdateDevice(self.UNITS['ExtractFanIntensivity'], 0, str(ExtractFanIntens), 0)
            UpdateDevice(self.UNITS['HeatExchanger'], 0, str(HeatExchanger), 0)
            UpdateDevice(self.UNITS['ElectricHeater'], 0, str(ElectricHeater), 0)
            UpdateDevice(self.UNITS['WaterHeater'], 0, str(WaterHeater), 0)
            UpdateDevice(self.UNITS['WaterCooler'], 0, str(WaterCooling), 0)
            UpdateDevice(self.UNITS['DXUnit'], 0, str(DXUnit), 0)
            UpdateDevice(self.UNITS['FiltersImupurity'], 0, str(FiltersImupurity), 0)

            CurrentPowerConsumption = int(MonitoringDataResult.registers[0+registersStartingOffset])
            CurrentHeaterPower = int(MonitoringDataResult.registers[1+registersStartingOffset])
            CurrentHeatRecovery = int(MonitoringDataResult.registers[2+registersStartingOffset])
            CurrentExchangeEfficiency = int(MonitoringDataResult.registers[3+registersStartingOffset])
            CurrentEnergySaving = int(MonitoringDataResult.registers[4+registersStartingOffset])

            decoder = BinaryPayloadDecoder.fromRegisters(MonitoringDataResult.registers,
                                               byteorder=Endian.Big)

            decoder.skip_bytes(6+17*2+5*4) # 6 * char + 17 * short + 5 * int
            TotalEnergyConsumtion = decoder.decode_32bit_uint()  # reg[11-12] from byte[21]
            UpdateDevice(self.UNITS['TotalEnergyConsumtion'], 0, str(CurrentPowerConsumption)+';'+str(TotalEnergyConsumtion), 0)

            decoder.skip_bytes(8)
            TotalHeaterConsumtion = decoder.decode_32bit_uint()  # reg[17-18] from byte[32]
            UpdateDevice(self.UNITS['TotalHeaterConsumtion'], 0, str(CurrentHeaterPower)+';'+str(TotalHeaterConsumtion), 0)

            decoder.skip_bytes(8)
            TotalEnergyRecovered = decoder.decode_32bit_uint()  # reg[23-24] from byte[44]
            UpdateDevice(self.UNITS['TotalEnergyRecovered'], 0, str(CurrentHeatRecovery)+';'+str(TotalEnergyRecovered), 0)

            temperature = ConvertToFloat(MonitoringDataResult, 25+registersStartingOffset)
            humidity = int(MonitoringDataResult.registers[26+registersStartingOffset])

            UpdateDevice(self.UNITS['CurrentExchangeEfficiency'], 0, str(CurrentExchangeEfficiency), 0)
            UpdateDevice(self.UNITS['CurrentEnergySaving'], 0, str(CurrentEnergySaving), 0)

            UpdateDevice(self.UNITS['Temp'], 0, str(temperature), 0)
            UpdateDevice(self.UNITS['Hum'], humidity, str(humidity), 0)

            if self.debug:
                Domoticz.Log("CurrentPowerConsumption: " + str(CurrentPowerConsumption))
                Domoticz.Log("CurrentHeaterPower: " + str(CurrentHeaterPower))
                Domoticz.Log("CurrentHeatRecovery: " + str(CurrentHeatRecovery))
                Domoticz.Log("CurrentExchangeEfficiency: " + str(CurrentExchangeEfficiency))
                Domoticz.Log("CurrentEnergySaving: " + str(CurrentEnergySaving))
                Domoticz.Log("CurrentEnergySaving: " + str(CurrentEnergySaving))
                Domoticz.Log("TotalEnergyConsumtion: " + str(TotalEnergyConsumtion))
                Domoticz.Log("TotalHeaterConsumtion: " + str(TotalHeaterConsumtion))
                Domoticz.Log("TotalEnergyRecovered: " + str(TotalEnergyRecovered))
                Domoticz.Log("Temperature: " + str(temperature))
                Domoticz.Log("Humidity: " + str(humidity))

        self.client.close()


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return


def UpdateDevice(Unit, nValue, sValue, TimedOut):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit in Devices:
        if Devices[Unit].nValue != nValue or Devices[Unit].sValue != sValue or Devices[Unit].TimedOut != TimedOut:
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            # Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return


def ConvertToFloat(data, reg):
    return float(ctypes.c_short(data.registers[reg]).value) / 10
