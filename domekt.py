# DOMEKT air supply plugin
"""
<plugin key="DOMEKT" name="Domekt" author="jarzyn" version="1.0.0" wikilink="" externallink="">
    <description>
        <h2>DOMEKT Roratory heat exchanger</h2><br/>
        This plygin allows to controll and monitor work parameters of Ventia's Rotatory heat exchagers.
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

from pymodbus.constants import Endian
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder

class BasePlugin:
    enabled = False
    debug = False
    AVAILABLE_LEVELS = [10,
                        20,
                        30,
                        40]

    UNITS = {
        'ECO':  1,
        'Auto': 2,
        'Temp': 3,
        'Hum':  4,
        'Mode': 5,
        'TotalEnergyConsumtion': 11,
        'TotalHeaterConsumtion': 12,
        'TotalEnergyRecovered': 13,
        'CurrentExchangeEfficiency': 14,
        'CurrentEnergySaving': 15
        }

    def __init__(self):
        return

    def onStart(self):

        # setup the appropriate logging level
        if Parameters['Mode6'] == "true":
            Domoticz.Debugging(1)
            DumpConfigToLog()
            self.debug = True
        else:
            Domoticz.Debugging(0)

        self.client = ModbusTcpClient(Parameters['Address'], port=int(Parameters['Port']))

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

        if Unit == self.UNITS['Mode'] and Command == 'Set Level':
            if Level in self.AVAILABLE_LEVELS:
                self.client.write_register(4, value=int(Level/10))
                UpdateDevice(Unit, Level, Level, 0)
                Domoticz.Log("Air flow mode changed")
            else:
                Domoticz.Log("Impossible to choose this mode")

            self.client.close()
            return

        if Command == 'Off':
            nVal = 0
        elif Command == 'On':
            nVal = 1

        if Unit == self.UNITS['ECO']:
            rAddr = 2
        elif Unit == self.UNITS['Auto']:
            rAddr = 3

        self.client.write_register(rAddr, value=nVal)
        UpdateDevice(Unit, nVal, Command, 0)
        self.client.close()

        # Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        self.client.connect()

        result = self.client.read_holding_registers(2, 3)
        if not result.isError():
            eco = int(result.registers[0])
            auto = int(result.registers[1])
            mode = int(result.registers[2]) * 10

            UpdateDevice(self.UNITS['ECO'], eco, str(eco), 0)
            UpdateDevice(self.UNITS['Auto'], auto,  str(auto), 0)
            UpdateDevice(self.UNITS['Mode'], mode, str(mode), 0)
            # Domoticz.Log("eco :" + str(eco) + " auto: " + str(auto))

        result = self.client.read_holding_registers(920, 27)
        if not result.isError():
            CurrentPowerConsumption = int(result.registers[0])
            CurrentHeaterPower = int(result.registers[1])
            CurrentHeatRecovery = int(result.registers[2])
            CurrentExchangeEfficiency = int(result.registers[3])
            CurrentEnergySaving = int(result.registers[4])

            decoder = BinaryPayloadDecoder.fromRegisters(result.registers,
                                               byteorder=Endian.Big)
            decoder.skip_bytes(20)
            TotalEnergyConsumtion = decoder.decode_32bit_uint()  # reg[11-12] from byte[21]
            UpdateDevice(self.UNITS['TotalEnergyConsumtion'], 0, str(CurrentPowerConsumption)+';'+str(TotalEnergyConsumtion), 0)

            decoder.skip_bytes(8)
            TotalHeaterConsumtion = decoder.decode_32bit_uint()  # reg[17-18] from byte[32]
            UpdateDevice(self.UNITS['TotalHeaterConsumtion'], 0, str(CurrentHeaterPower)+';'+str(TotalHeaterConsumtion), 0)

            decoder.skip_bytes(8)
            TotalEnergyRecovered = decoder.decode_32bit_uint()  # reg[23-24] from byte[44]
            UpdateDevice(self.UNITS['TotalEnergyRecovered'], 0, str(CurrentHeatRecovery)+';'+str(TotalEnergyRecovered), 0)

            temperature = float(result.registers[25]) / 10
            humidity = int(result.registers[26])

            UpdateDevice(self.UNITS['CurrentExchangeEfficiency'], 0, str(CurrentExchangeEfficiency), 0)
            UpdateDevice(self.UNITS['CurrentEnergySaving'], 0, str(CurrentEnergySaving), 0)

            UpdateDevice(self.UNITS['Temp'], 0, str(temperature), 0)
            UpdateDevice(self.UNITS['Hum'], humidity, str(humidity), 0)

        self.client.close()
        if False:
            Domoticz.Log("CurrentPowerConsumption: " + str(CurrentPowerConsumption))
            Domoticz.Log("CurrentHeaterPower: " + str(CurrentHeaterPower))
            Domoticz.Log("CurrentHeatRecovery: " + str(CurrentHeatRecovery))
            Domoticz.Log("CurrentExchangeEfficiency: " + str(CurrentExchangeEfficiency))
            Domoticz.Log("CurrentEnergySaving: " + str(CurrentEnergySaving))
            Domoticz.Log("CurrentEnergySaving: " + str(CurrentEnergySaving))
            Domoticz.Log("TotalEnergyConsumtion: " + str(TotalEnergyConsumtion))
            Domoticz.Log("TotalHeaterConsumtion: " + str(TotalHeaterConsumtion))
            Domoticz.Log("TotalEnergyRecovered: " + str(TotalEnergyRecovered))
            Domoticz.Log("temperature: " + str(temperature))
            Domoticz.Log("humidity: " + str(humidity))

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

