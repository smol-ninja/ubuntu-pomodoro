import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import GObject as gobject
import signal
import os, subprocess, time
from datetime import datetime
import controls

APPINDICATOR_ID = 'Pomodoro'
WORK_TIME = 0.5
SHORT_BREAK = 0.2
LONG_BREAK = 0.3
STREAK_LENGTH = 2

class UbuntuIndicator(object):
    streak = 0
    yesterday_streak = 0
    startdate = datetime.now().day
    timer = 0
    PD = 'pomodoro'
    LB = 'long_break'
    SB = 'short_break'

    def build_menu(self):
        self.menu = gtk.Menu()
        self.item_start = gtk.MenuItem('Start')
        self.item_start.connect('activate', self.start)
        self.menu.append(self.item_start)
        self.item_resume = gtk.MenuItem('Resume')
        self.item_resume.connect('activate', self.resume)
        self.menu.append(self.item_resume)
        self.item_pause = gtk.MenuItem('Pause')
        self.item_pause.connect('activate', self.pause)
        self.menu.append(self.item_pause)
        self.item_stop = gtk.MenuItem('Stop')
        self.item_stop.connect('activate', self.stop)
        self.menu.append(self.item_stop)
        self.menu.append(gtk.SeparatorMenuItem())
        item_pomodoro = gtk.MenuItem('Pomodoro')
        item_pomodoro.connect('activate', self.pomodoro)
        self.menu.append(item_pomodoro)
        item_short_break = gtk.MenuItem('Short Break')
        item_short_break.connect('activate', self.short_break)
        self.menu.append(item_short_break)
        item_long_break = gtk.MenuItem('Long Break')
        item_long_break.connect('activate', self.long_break)
        self.menu.append(item_long_break)
        self.menu.append(gtk.SeparatorMenuItem())
        self.item_streak = gtk.MenuItem('Day Streak: %s' % (self.streak, ))
        self.menu.append(self.item_streak)
        self.item_yest_streak = gtk.MenuItem('Yesterday Streak: %s' % (self.yesterday_streak, ))
        self.menu.append(self.item_yest_streak)
        self.menu.append(gtk.SeparatorMenuItem())
        item_reset = gtk.MenuItem('Reset')
        item_reset.connect('activate', self.reset)
        self.menu.append(item_reset)
        item_quit = gtk.MenuItem('Quit')
        item_quit.connect('activate', self.quit)
        self.menu.append(item_quit)

        self.menu.show_all()
        self.item_resume.hide()
        self.item_pause.hide()
        self.item_stop.hide()
        return self.menu

    def quit(self, source):
        gtk.main_quit()

    def start(self, source):
        self.item_start.hide()
        self.item_pause.show()
        self.item_stop.show()
        if datetime.now().day - self.startdate >= 1:
            self.reset()
        self.work_time()

    def get_icon(self, name=None, iconName=None):
        if iconName is not None:
            return os.path.abspath('icons/'+iconName)

        if self.event == self.PD:
            ext = str(5*int((20*self.timer // (WORK_TIME*60))) % 100)
            if len(ext) == 1:
                ext = '00' + ext
            elif len(ext) == 2:
                ext = '0' + ext
            if name == 'paused':
                return os.path.abspath('icons/'+'pomodoro-paused-'+ext+'.svg')
            else:
                return os.path.abspath('icons/'+'pomodoro-'+ext+'.svg')

        else:
            if self.event == self.SB:
                ext = str(5*int((20*self.timer // (SHORT_BREAK*60))) % 100)
            if self.event == self.LB:
                ext = str(5*int((20*self.timer // (LONG_BREAK*60))) % 100)
            if len(ext) == 1:
                ext = '00' + ext
            elif len(ext) == 2:
                ext = '0' + ext
            if name == 'paused':
                return os.path.abspath('icons/'+'break-paused-'+ext+'.svg')
            else:
                return os.path.abspath('icons/'+'break-'+ext+'.svg')

    def work_time(self):
        try:
            gobject.source_remove(self.source_id)
        except:
            pass
        self.reset_timer()
        self.event = self.PD
        self.indicator.set_icon(self.get_icon())
        subprocess.call(['notify-send', 'Pomodoro', 'Focus on your work.'])
        self.source_id = gobject.timeout_add(1000, self.start_pomodoro_timer)

    def start_pomodoro_timer(self):
        self.timer += 1
        self.indicator.set_icon(self.get_icon())

        if self.timer > WORK_TIME*60:
            self.streak += 1
            self.item_streak.set_label('Day Streak: %s' % (self.streak, ))
            if self.streak % STREAK_LENGTH == 0:
                self.break_time(LONG_BREAK)
            else:
                self.break_time(SHORT_BREAK)
        return True

    def start_break_timer(self, breakTime):
        self.timer += 1
        self.indicator.set_icon(self.get_icon())
        cur_pos = gdk.get_default_root_window().get_pointer()
        if self.timer > breakTime*60:
            while cur_pos == gdk.get_default_root_window().get_pointer():
                time.sleep(0.5)
            self.work_time()
        return True

    def reset_timer(self):
        self.timer = 0

    def pomodoro(self, source):
        self.work_time()

    def pause(self, source):
        gobject.source_remove(self.source_id)
        self.indicator.set_icon(self.get_icon(name='paused'))

        self.item_pause.hide()
        self.item_resume.show()

    def stop(self, source):
        self.item_pause.hide()
        self.item_resume.hide()
        self.item_stop.hide()
        self.item_start.show()

        gobject.source_remove(self.source_id)

    def resume(self, source):
        if self.event == self.PD:
            self.source_id = gobject.timeout_add(1000, self.start_pomodoro_timer)
        elif self.event == self.SB:
            self.source_id = gobject.timeout_add(1000, self.start_break_timer, SHORT_BREAK)
        elif self.event == self.LB:
            self.source_id = gobject.timeout_add(1000, self.start_break_timer, LONG_BREAK)

        self.item_pause.show()
        self.item_resume.hide()

    def short_break(self, source):
        self.item_start.hide()
        self.item_resume.hide()
        self.item_pause.show()
        self.item_stop.show()

        self.break_time(SHORT_BREAK)

    def long_break(self, source):
        self.item_start.hide()
        self.item_resume.hide()
        self.item_pause.show()
        self.item_stop.show()

        self.break_time(LONG_BREAK)

    def break_time(self, breakTime=SHORT_BREAK):
        self.reset_timer()
        try:
            gobject.source_remove(self.source_id)
        except:
            pass
        if breakTime == SHORT_BREAK:
            self.event = self.SB
            self.indicator.set_icon(self.get_icon())
            subprocess.call(['notify-send', 'Pomodoro', 'Take a short break: %s minutes' % (SHORT_BREAK, )])
            self.source_id = gobject.timeout_add(1000, self.start_break_timer, SHORT_BREAK)
        else:
            self.event = self.LB
            self.indicator.set_icon(self.get_icon())
            subprocess.call(['notify-send', 'Pomodoro', 'Take a Long break: %s minutes' % (LONG_BREAK, )])
            self.source_id = gobject.timeout_add(1000, self.start_break_timer, LONG_BREAK)

    def reset(self, source):
        self.yesterday_streak = self.steak
        self.streak = 0
        self.item_yest_streak.set_label('Yesterday Streak: %s' % (self.yesterday_streak, ))
        self.item_streak.set_label('Day Streak: %s' % (self.streak, ))
        self.startdate = datetime.now().day
        self.reset_timer()
        self.indicator.set_icon(self.get_icon(iconName='break-000.svg'))
        try:
            gobject.source_remove(self.source_id)
        except:
            pass

    def run(self):
        self.indicator = appindicator.Indicator.new(APPINDICATOR_ID, self.get_icon(iconName='break-000.svg'), appindicator.IndicatorCategory.SYSTEM_SERVICES)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())
        gobject.timeout_add(1000, self.update_label)
        gtk.main()

    def update_label(self):
        minute = str(WORK_TIME - int(self.timer // 60))
        if len(minute) == 1:
            minute = '0'+minute
        second = str(60 - int(self.timer % 60))
        if len(second) == 1:
            second = '0'+second
        self.indicator.set_label(minute+':'+second, 'pomodoro')
        return True

if __name__=='__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    UbuntuIndicator().run()