import time

class thisButton:
    def __init__(self):
        
        self.prev_state = None
        self.activated_state = True

        self.cur_time = None
        self.prev_state_change = None
        self.active = None
        self.long_press_activated = False
        self.debounce_start = None
        self.debouncing = False
        self.held = False
        
        self.click_function = None
        self.long_press_start_function = None
        self.long_press_release_function = None
        self.held_function = None
        self.click_only_assigned = False

        self.default_debounce_threshold =   2000000
        self.default_long_press_threshold = 500000000
        self.default_held_interval =        100000000

        self.debounce_threshold = self.default_debounce_threshold
        self.long_press_threshold = self.default_long_press_threshold
        self.held_interval = self.default_held_interval
        self.held_next_time = 0

        self.debug = False
    
    def time_monotonic_ns(self):
        return time.ticks_us() * 1000
    
    #this needs to be called frequently from the main loop
    def tick(self, gpio_state):
        #read the pin and log the time, if not in a debounce waiting period
        self.cur_time = self.time_monotonic_ns()
        if self.debouncing == False:
            self.cur_state = gpio_state
            if self.cur_state != self.prev_state:
                self.start_debounce()
        
        #check debounce
        if self.debouncing == True and self.cur_time > self.debounce_start + self.debounce_threshold:
            #time is up, stop blocking for debounce
            self.debouncing = False

        if self.cur_state == self.activated_state: #button is active this cycle
            
            #the button was just pressed, start counting
            if self.active != True: 
                self.active = True
                self.prev_state_change = self.cur_time
                if self.debug == True: print("Click Down")
                #if only click is defined, can fire the event now
                if self.click_function is not None and self.click_only_assigned == True: self.click_function()
                
            elif self.active == True: #this is the second or more cycle where the button has been pressed
                if self.cur_time - self.prev_state_change > self.long_press_threshold: #check if this exceeds the long press threshold
                    if self.long_press_activated != True and self.long_press_start_function is not None:
                        if self.debug == True: print("Long press start Detected")
                        self.long_press_activated = True
                        self.active = False #stops more detections until the button is released
                        #fire the long press start event at this point
                        if self.long_press_start_function is not None: self.long_press_start_function()
                        
                    elif self.held_function is not None:
                        self.long_press_activated = True
                        #fire the hold function if this is the first iteration and start counting
                        if self.held == False:
                            self.held = True
                            self.held_function()
                            self.held_next_time = self.cur_time + self.held_interval
                        #or fire it because this is a subsequent iteration
                        elif self.cur_time > self.held_next_time:
                            self.held_function()
                            self.held_next_time = self.cur_time + self.held_interval
                            

        #button was just released (and not a bounce)
        elif self.cur_state != self.activated_state and self.active == True: 
            #Long press release
            if self.long_press_activated == True: 
                self.long_press_activated = False
                self.active = False
                self.held = False
                if self.long_press_release_function is not None: self.long_press_release_function()
                if self.debug == True: print("Long press or hold duration: " + str(self.cur_time - self.prev_state_change))
                
            #Click release
            else: 
                self.active = False
                if self.click_function is not None and self.click_only_assigned == False: self.click_function()
                if self.debug == True: print("Click release, duration: " + str(self.cur_time - self.prev_state_change))
            
        self.prev_state = self.cur_state

    def msToNs(self, milliseconds):
        #helper to convert ms to ns
        return milliseconds * 1000000

    def nsToMs(self, nanoseconds):
        #helper to convert ns to ms
        return nanoseconds / 1000000

    def start_debounce(self):
        self.debouncing = True
        self.debounce_start = self.cur_time

    def assignClick(self, function_name):
        #this function will fire when the button is pressed if no other functions are assigned, otherwise it fires on button release
        self.click_function = function_name
        if self.long_press_start_function is None and self.long_press_release_function is None and self.held_function is None:
            self.click_only_assigned = True

    def assignLongPressStart(self, function_name):
        self.long_press_start_function = function_name
        self.click_only_assigned = False

    def assignLongPressRelease(self, function_name):
        #this fires when the button is released after either a long press or when it is held down
        self.long_press_release_function = function_name
        self.click_only_assigned = False

    def assignHeld(self, function_name, milliseconds = -1):
        #this fires repeatedly at an interval while the button is held down
        #omit milliseconds and a default value will be used
        self.held_function = function_name
        self.click_only_assigned = False
        if milliseconds < 0:
            self.held_interval = self.default_held_interval
        else:
            self.held_interval = self.msToNs(milliseconds)

    def toggleDebug(self):
        #add some print statements to help dialing in timing or troubleshoot
        self.debug = not self.debug

    def setDebounceThreshold(self, milliseconds = -1):
        #change the debounce threshold.  Omit milliseconds to reset to default
        if milliseconds < 0:
            self.debounce_threshold = self.default_debounce_threshold
        else:
            self.debounce_threshold = self.msToNs(milliseconds)

    def setLongPressThreshold(self, milliseconds = -1):
        #change the long press threshold.  Omit milliseconds to reset to default
        if milliseconds < 0:
            self.long_press_threshold = self.default_long_press_threshold
        else:
            self.long_press_threshold = self.msToNs(milliseconds)

    def setHeldInterval(self, milliseconds = -1):
        #change the repeat interval while button is held down.  Omit milliseconds to reset to default
        if milliseconds < 0:
            self.held_interval = self.default_held_interval
        else:
            self.held_interval = self.msToNs(milliseconds)

    @property
    def isHeld(self):
        #Return true if a long press or hold is active
        return self.long_press_activated

    @property
    def heldDuration(self):
        #return the amount of time in milliseconds that a button is currently held, or zero if it is not
        if self.long_press_activated == True:
            return self.nsToMs((self.time_monotonic_ns() - self.prev_state_change))
        else:
            return 0

    @property
    def buttonActive(self):
        #returns true while the button is currently pressed after debouncing, not necessarily during a long press
        return self.active