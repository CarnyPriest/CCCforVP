##   ____           _                ____
##  / ___|__ _  ___| |_ _   _ ___   / ___|__ _ _ __  _   _  ___  _ __
## | |   / _` |/ __| __| | | / __| | |   / _` | '_ \| | | |/ _ \| '_ \
## | |__| (_| | (__| |_| |_| \__ \ | |__| (_| | | | | |_| | (_) | | | |
##  \____\__,_|\___|\__|\__,_|___/  \____\__,_|_| |_|\__, |\___/|_| |_|
##                                                   |___/
##           ___ ___  _  _ _____ ___ _  _ _   _ ___ ___
##          / __/ _ \| \| |_   _|_ _| \| | | | | __|   \
##         | (_| (_) | .` | | |  | || .` | |_| | _|| |) |
##          \___\___/|_|\_| |_| |___|_|\_|\___/|___|___/
##
## A P-ROC Project by Eric Priepke, Copyright 2012-2013
## Built on the PyProcGame Framework from Adam Preble and Gerry Stellenberg
## Original Cactus Canyon software by Matt Coriale
##

import ep
from procgame import dmd
import os
import shutil
from distutils import dir_util
import sys

class ServiceModeSkeleton(ep.EP_Mode):
    """Service Mode List base class."""
    def __init__(self, game, priority, font):
        super(ServiceModeSkeleton, self).__init__(game, priority)
        self.name = ""
        self.title_layer = dmd.TextLayer(1, 1, font, "left")
        self.item_layer = dmd.TextLayer(128/2, 12, font, "center")
        self.instruction_layer = dmd.TextLayer(1, 25, font, "left")
        self.layer = dmd.GroupedLayer(128, 32, [self.title_layer, self.item_layer, self.instruction_layer])
        self.no_exit_switch = game.machine_type == 'sternWhitestar'

    def mode_started(self):
        self.title_layer.set_text(str(self.name))
        self.game.sound.play(self.game.assets.sfx_serviceStart)

    def mode_stopped(self):
        self.game.sound.play(self.game.assets.sfx_menuExit)
        # save the data
        self.game.save_game_data()
        if self.game.service_mode not in self.game.modes:
            #print "Service Mode Exiting"
            if self.game.usb_update:
                #print "Reloading to pull in new files"
                sys.exit(42)
            else:
                #print "Calling Reset"
                self.game.reset()

    def disable(self):
        pass

    def sw_down_active(self, sw):
        if self.game.switches.enter.is_active():
            self.game.modes.remove(self)
            return True

    def sw_exit_active(self, sw):
        self.game.modes.remove(self)
        return True

class ServiceModeList(ServiceModeSkeleton):
    """Service Mode List base class."""
    def __init__(self, game, priority, font):
        super(ServiceModeList, self).__init__(game, priority, font)
        self.items = []

    def mode_started(self):
        super(ServiceModeList, self).mode_started()

        self.iterator = 0
        self.change_item()

    def change_item(self):
        ctr = 0
        for item in self.items:
            if (ctr == self.iterator):
                self.item = item
            ctr += 1
        self.max = ctr - 1
        self.item_layer.set_text(self.item.name)

    def sw_up_active(self,sw):
        if self.game.switches.enter.is_inactive():
            self.item.disable()
            if (self.iterator < self.max):
                self.iterator += 1
            self.game.sound.play(self.game.assets.sfx_menuUp)
            self.change_item()
        return True

    def sw_down_active(self,sw):
        if self.game.switches.enter.is_inactive():
            self.item.disable()
            if (self.iterator > 0):
                self.iterator -= 1
            self.game.sound.play(self.game.assets.sfx_menuDown)
            self.change_item()
        elif self.no_exit_switch:
            self.exit()
        return True

    def sw_enter_active(self,sw):
        self.game.modes.add(self.item)
        return True

    def exit(self):
        self.item.disable()
        self.game.modes.remove(self)
        return True

class ServiceMode(ServiceModeList):
    """Service Mode."""
    def __init__(self, game, priority, font, extra_tests=[]):
        super(ServiceMode, self).__init__(game, priority,font)
        self.name = 'Service Mode'
        self.instruction_layer.set_text("Revision: " + self.game.revision)
        self.tests = Tests(self.game, self.priority+1, font, extra_tests)
        self.items = [self.tests]
        if len(self.game.settings) > 0:
            ##print "Service - Adding Settings"
            self.settings = Settings(self.game, self.priority+1, font, 'Settings', self.game.settings)
            self.items.append(self.settings)
        if len(self.game.game_data) > 0:
            ##print "Service - Adding statistics"
            self.statistics = Statistics(self.game, self.priority+1, font, 'Statistics', self.game.game_data)
            self.items.append(self.statistics)
        if self.game.usb_update:
            self.update = Update(self.game,self.priority+1, font, 'Update')
            self.items.append(self.update)
        if self.game.shutdownFlag:
            self.shutdown = Shutdown(self.game,self.priority+1, font, 'Shutdown')
            self.items.append(self.shutdown)

class Shutdown(ServiceModeList):
    def __init__(self, game, priority, font, title):
        super(Shutdown, self).__init__(game,priority, font)
        self.name = title
        self.items = []
        self.do_shutdown = DoShutdown(self.game,self.priority+1, font)
        self.items.append(self.do_shutdown)

class ShutdownItem:
    """Service Mode."""
    def __init__(self, name):
        self.name = name

    def disable(self):
        pass

class DoShutdown(ServiceModeList):
    def __init__(self,game,priority, font):
        super(DoShutdown,self).__init__(game,priority,font)
        self.name = "PRESS ENTER TO CONFIRM"
        self.items = []
        self.items.append( ShutdownItem("ONE MORE TO POWER OFF"))

    def mode_started(self):
        super(DoShutdown, self).mode_started()

    def sw_enter_active(self,sw):
        #print "Powering off"
        # exit with error code 69
        sys.exit(69)

class Update(ServiceModeList):
    """USB Code Update"""
    def __init__(self, game, priority, font, title):
        super(Update, self).__init__(game, priority, font)
        self.name = title
        self.items = []
        self.do_update = DoUpdate(self.game,self.priority+1,font)
        self.items.append(self.do_update)


class DoUpdate(ServiceModeList):
    """ USB Updater"""
    def __init__(self,game,priority, font):
        super(DoUpdate,self).__init__(game,priority,font)

        self.myLocation = None
        self.okToUpdate = False
        self.items = []
        # list the contents of the USB path
        dirs = os.listdir(self.game.usb_location)
        # check them all for the update files
        for directory in dirs:
            checkThis = self.game.usb_location + directory + "/ccc_update_files"
            if os.path.isdir(checkThis):
                #print "Found the update"
                self.myLocation = checkThis
        if self.myLocation != None:
            self.okToUpdate = True
            self.name = "FILES UPDATE"
            self.items.append( UpdateItem("PRESS ENTER TO UPDATE"))
        else:
            self.okToUpdate = False
            #print "Didn't find the update"
            self.name = "FILES UPDATE"
            self.items.append( UpdateItem("FILES NOT FOUND"))

    def mode_started(self):
        super(DoUpdate, self).mode_started()

    def mode_stopped(self):
        self.game.sound.play(self.game.assets.sfx_menuExit)

    def sw_enter_active(self,sw):
        #print "Derp"
        if self.okToUpdate:
            # if enter is pressed, copy the files
            # update the layer to say copying files
            self.item_layer.set_text("COPYING FILES")
            self.instruction_layer.set_text("DO NOT POWER OFF")
            self.delay(delay=1,handler=self.copy_files)
        else:
            self.game.sound.play(self.game.assets.sfx_menuReject)
        return True

    def copy_files(self):
            dir_util.copy_tree(self.myLocation,self.game.game_location)
            self.item_layer.set_text("FINISHED")
            self.instruction_layer.set_text("")

class UpdateItem:
    """Service Mode."""
    def __init__(self, name):
        self.name = name

    def disable(self):
        pass


class Tests(ServiceModeList):
    """Service Mode."""
    def __init__(self, game, priority, font, extra_tests=[]):
        super(Tests, self).__init__(game, priority,font)
        #self.title_layer.set_text('Tests')
        self.name = 'Tests'
        self.lamp_test = LampTest(self.game, self.priority+1, font)
        self.coil_test = CoilTest(self.game, self.priority+1, font)
        self.switch_test = SwitchTest(self.game, self.priority+1, font)
        self.items = [self.switch_test, self.lamp_test, self.coil_test]
        for test in extra_tests:
            self.items.append(test)

class LampTest(ServiceModeList):
    """Lamp Test"""
    def __init__(self, game, priority, font):
        super(LampTest, self).__init__(game, priority,font)
        self.name = "Lamp Test"
        self.items = self.game.lamps

    def change_item(self):
        super(LampTest, self).change_item()
        self.item.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

    def sw_enter_active(self,sw):
        return True


class CoilTest(ServiceModeList):
    """Coil Test"""
    def __init__(self, game, priority, font):
        super(CoilTest, self).__init__(game, priority, font)
        self.name = "Coil Test"
        self.title_layer.set_text('Coil Test - Enter btn: mode')
        self.instruction_layer.set_text('Pulse with start button')
        self.items = self.game.coils

    def mode_started(self):
        super(CoilTest, self).mode_started()
        self.action = 'manual'
        if self.game.lamps.has_key('startButton'): self.game.lamps.startButton.schedule(schedule=0xff00ff00, cycle_seconds=0, now=False)
        self.delay(name='auto', event_type=None, delay=2.0, handler=self.process_auto)

    def process_auto(self):
        if (self.action == 'auto'):
            self.item.pulse(20)
        self.delay(name='auto', event_type=None, delay=2.0, handler=self.process_auto)


    def sw_enter_active(self,sw):
        if (self.action == 'manual'):
            self.action = 'auto'
            if self.game.lamps.has_key('startButton'): self.game.lamps.startButton.disable()
            self.instruction_layer.set_text('Auto pulse')
        elif (self.action == 'auto'):
            self.action = 'manual'
            if self.game.lamps.has_key('startButton'): self.game.lamps.startButton.schedule(schedule=0xff00ff00, cycle_seconds=0, now=False)
            self.instruction_layer.set_text('Pulse with start button')
        return True

    def sw_startButton_active(self,sw):
        if (self.action == 'manual'):
            self.item.pulse(20)
        return True

class SwitchTest(ServiceModeSkeleton):
    """Switch Test"""
    def __init__(self, game, priority, font):
        super(SwitchTest, self).__init__(game, priority,font)
        self.name = "Switch Test"
        for switch in self.game.switches:
            if self.game.machine_type == 'sternWhitestar':
                add_handler = 1
            elif switch != self.game.switches.exit:
                add_handler = 1
            else:
                add_handler = 0
            if add_handler:
                self.add_switch_handler(name=switch.name, event_type='inactive', delay=None, handler=self.switch_handler)
                self.add_switch_handler(name=switch.name, event_type='active', delay=None, handler=self.switch_handler)

    def switch_handler(self, sw):
        if (sw.state):
            self.game.sound.play(self.game.assets.sfx_menuSwitchEdge)
        self.item_layer.set_text(sw.name + ' - ' + str(sw.state))
        return True

    def sw_enter_active(self,sw):
        return True

class Statistics(ServiceModeList):
    """Service Mode."""
    def __init__(self, game, priority, font, name, itemlist):
        super(Statistics, self).__init__(game, priority,font)
        #self.title_layer.set_text('Settings')
        self.name = name
        self.items = []
        for section in itemlist:
            if section == "Audits":
                ##print "adding " + section
                self.items.append( StatsDisplay( self.game, priority + 1, font, str(section),itemlist[section] ))

class StatsDisplay(ServiceModeList):
    """Stats Display"""
    def __init__(self, game, priority, font, name, itemlist):
        super(StatsDisplay, self).__init__(game, priority, font)
        self.name = name
        self.value_layer = dmd.TextLayer(128/2, 22, font, "center")
        self.items = []
        #print itemlist
        for item in sorted(itemlist.iterkeys()):
                self.items.append( StatsItem(str(item), itemlist[item]) )
        self.layer = dmd.GroupedLayer(128, 32, [self.title_layer, self.item_layer, self.value_layer])

    def mode_started(self):
        super(StatsDisplay, self).mode_started()

    def change_item(self):
        super(StatsDisplay, self).change_item()
        try:
            self.item.score
        except:
            self.item.score = 'None'

        if self.item.score == 'None':
            self.value_layer.set_text(str(self.item.value))
        else:
            self.value_layer.set_text(self.item.value + ": " + str(self.item.score))

    def sw_enter_active(self, sw):
        return True

class StatsItem:
    """Service Mode."""
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def disable(self):
        pass

class HighScoreItem:
    """Service Mode."""
    def __init__(self, name, value, score):
        self.name = name
        self.value = value
        self.score = score

    def disable(self):
        pass


class SwitchTest(ServiceModeSkeleton):
    """Switch Test"""
    def __init__(self, game, priority, font):
        super(SwitchTest, self).__init__(game, priority,font)
        self.name = "Switch Test"
        for switch in self.game.switches:
            if self.game.machine_type == 'sternWhitestar':
                add_handler = 1
            elif switch != self.game.switches.exit:
                add_handler = 1
            else:
                add_handler = 0
            if add_handler:
                self.add_switch_handler(name=switch.name, event_type='inactive', delay=None, handler=self.switch_handler)
                self.add_switch_handler(name=switch.name, event_type='active', delay=None, handler=self.switch_handler)

    def switch_handler(self, sw):
        if (sw.state):
            self.game.sound.play(self.game.assets.sfx_menuSwitchEdge)
        self.item_layer.set_text(sw.name + ' - ' + str(sw.state))
        return True

    def sw_enter_active(self,sw):
        return True


class Settings(ServiceModeList):
    """Service Mode."""
    def __init__(self, game, priority, font, name, itemlist):
        super(Settings, self).__init__(game, priority,font)
        #self.title_layer.set_text('Settings')
        self.name = name
        self.items = []
        self.font = font
        for section in sorted(itemlist.iterkeys()):
            self.items.append( SettingsEditor( self.game, priority + 1, font, str(section),itemlist[section] ))

class SettingsEditor(ServiceModeList):
    """Service Mode."""
    def __init__(self, game, priority, font, name, itemlist):
        super(SettingsEditor, self).__init__(game, priority, font)
        self.title_layer = dmd.TextLayer(1, 1, font, "left")
        self.item_layer = dmd.TextLayer(128/2, 12, font, "center")
        self.instruction_layer = dmd.TextLayer(1, 25, font, "left")
        self.no_exit_switch = game.machine_type == 'sternWhitestar'
        #self.title_layer.set_text('Settings')
        self.name = name
        self.items = []
        self.value_layer = dmd.TextLayer(128/2, 19, font, "center")
        self.layer = dmd.GroupedLayer(128, 32, [self.title_layer, self.item_layer, self.value_layer, self.instruction_layer])
        for item in sorted(itemlist.iterkeys()):
            #self.items.append( EditItem(str(item), itemlist[item]['options'], itemlist[item]['value'] ) )
            if 'increments' in itemlist[item]:
                num_options = (itemlist[item]['options'][1]-itemlist[item]['options'][0]) / itemlist[item]['increments']
                option_list = []
                for i in range(0,num_options):
                    option_list.append(itemlist[item]['options'][0] + (i * itemlist[item]['increments']))
                self.items.append( EditItem(str(item), option_list, self.game.user_settings[self.name][item]) )
            else:
                self.items.append( EditItem(str(item), itemlist[item]['options'], self.game.user_settings[self.name][item]) )
        self.state = 'nav'
        self.stop_blinking = True
        self.item = self.items[0]
        self.value_layer.set_text(str(self.item.value))
        self.option_index = self.item.options.index(self.item.value)

    def mode_started(self):
        super(SettingsEditor, self).mode_started()

    def mode_stopped(self):
        self.game.sound.play(self.game.assets.sfx_menuExit)

    def sw_enter_active(self, sw):
        if not self.no_exit_switch:
            self.process_enter()
        return True

    def process_enter(self):
        if self.state == 'nav':
            self.state = 'edit'
            self.blink = True
            self.stop_blinking = False
            self.delay(name='blink', event_type=None, delay=.3, handler=self.blinker)
        else:
            self.state = 'nav'
            self.instruction_layer.set_text("Change saved")
            self.delay(name='change_complete', event_type=None, delay=1, handler=self.change_complete)
            self.game.sound.play(self.game.assets.sfx_menuSave)
            self.game.user_settings[self.name][self.item.name]=self.item.value
            self.stop_blinking = True
            self.game.save_settings()

    def sw_exit_active(self, sw):
        self.process_exit()
        return True

    def process_exit(self):
        if self.state == 'nav':
            self.game.modes.remove(self)
        else:
            self.state = 'nav'
            self.value_layer.set_text(str(self.item.value))
            self.stop_blinking = True
            self.game.sound.play(self.game.assets.sfx_menuCancel)
            self.instruction_layer.set_text("Change cancelled")
            self.delay(name='change_complete', event_type=None, delay=1, handler=self.change_complete)

    def sw_up_active(self, sw):
        if self.game.switches.enter.is_inactive():
            self.process_up()

        else:
            self.process_enter()
        return True

    def process_up(self):
        if self.state == 'nav':
            self.item.disable()
            if (self.iterator < self.max):
                self.iterator += 1
            self.game.sound.play(self.game.assets.sfx_menuUp)
            self.change_item()
        else:
            if self.option_index < (len(self.item.options) - 1):
                self.option_index += 1
                self.item.value = self.item.options[self.option_index]
                self.value_layer.set_text(str(self.item.value))


    def sw_down_active(self, sw):
        if self.game.switches.enter.is_inactive():
            self.process_down()
        else:
            self.process_exit()
        return True

    def process_down(self):
        if self.state == 'nav':
            self.item.disable()
            if (self.iterator > 0):
                self.iterator -= 1
            self.game.sound.play(self.game.assets.sfx_menuDown)
            self.change_item()
        else:
            if self.option_index > 0:
                self.option_index -= 1
                self.item.value = self.item.options[self.option_index]
                self.value_layer.set_text(str(self.item.value))

    def change_item(self):
        ctr = 0
        for item in self.items:
            if ctr == self.iterator:
                self.item = item
            ctr += 1
        self.max = ctr - 1
        self.item_layer.set_text(self.item.name)
        self.value_layer.set_text(str(self.item.value))
        self.option_index = self.item.options.index(self.item.value)

    def disable(self):
        pass

    def blinker(self):
        if self.blink:
            self.value_layer.set_text(str(self.item.value))
            self.blink = False
        else:
            self.value_layer.set_text("")
            self.blink = True
        if not self.stop_blinking:
            self.delay(name='blink', event_type=None, delay=.3, handler=self.blinker)
        else:
            self.value_layer.set_text(str(self.item.value))

    def change_complete(self):
        self.instruction_layer.set_text("")

class EditItem:
    """Service Mode."""
    def __init__(self, name, options, value):
        self.name = name
        self.options = options
        self.value = value

    def disable(self):
        pass
