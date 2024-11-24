# This file is part of NoCurve.
#
#    NoCurve is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    NoCurve is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with NoCurve.  If not, see <http://www.gnu.org/licenses/>.

##
## MVC classes
##

import functools

def virtualmethod(func):
    @functools.wraps(func)
    def wrapper(self, *a, **k):
        raise NotImplementedError("not implemented virtual method called: %s" % func.__name__)
    return wrapper

class QueuedSet(set):
    def __init__(self, *args, **kwargs):
        set.__init__(self, *args, **kwargs)
        self._add_queue = set()
        self._rem_queue = set()
        self._dirty = False
        
    def add(self, item):
        if item not in self:
            self._add_queue.add(item)
            self._dirty = True
            
    def remove(self, item):
        if item in self:
            self._rem_queue.add(item)
            self._dirty = True
            
    def __iter__(self):
        if self._dirty:
            self.difference_update(self._rem_queue)
            self.update(self._add_queue)
            self._rem_queue.clear()
            self._add_queue.clear()
            self._dirty = False
        return set.__iter__(self)

class EventMeta(type):
    _classes_ = {}
    
    def __new__(meta, name, bases, dct):
        if name != 'Event':
            assert name not in EventMeta._classes_, ValueError("Event class already registered")
        
        cls = type.__new__(meta, name, bases, dct)
        
        if name != 'Event':
            EventMeta._classes_[name] = cls
            
        return cls
    
    @staticmethod
    def get_event_by_name(name):
        return EventMeta._classes_.get(name)

get_event_by_name = EventMeta.get_event_by_name

class Event(object):
    __metaclass__ = EventMeta
    
    def __init__(self):
        self._listeners = QueuedSet()
        
    def register(self, listener):
        self._listeners.add(listener)
        
    def unregister(self, listener):
        self._listeners.remove(listener)
        
    def emit(self, *args, **kwargs):
        for listener in self._listeners:
            if listener(*args, **kwargs):
                break

class Container(object):
    def __init__(self, component):
        self.facade = Facade.get_facade()
        self.component = component
        
    def on_register(self): pass
    
    def emit_event(self, event, *args, **kwdargs):
        event.emit(*args, **kwdargs)

class Mediator(Container):
    pass

class Proxy(Container):
    pass

class Singleton(object):
    __instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls, *args, **kwargs)
            print "[NEW] Instance of %s: %s" % (cls.__name__, cls.__instance)
        return cls.__instance
        
    @classmethod
    def get_instance(cls):
        return cls.__instance

class Model(Singleton):
    __proxies = {}
    
    def __init__(self):
        Singleton.__init__(self)
        self.facade = Facade.get_facade()
    
    @classmethod
    def add_proxy(cls, proxy):
        if proxy.NAME not in cls.__proxies:
            cls.__proxies[proxy.NAME] = proxy
            proxy.on_register()
        
    @classmethod
    def remove_proxy(cls, proxy):
        if proxy in cls.__proxies:
            proxy.on_unregister()
            cls.__proxies.pop(proxy.NAME)
    
    @classmethod
    def get_proxy(cls, name):
        return cls.__proxies[name]
        
    @classmethod
    def has_proxy(cls, name):
        return name in cls.__proxies

class View(Singleton):
    __mediators = {}
    
    def __init__(self):
        Singleton.__init__(self)
        self.facade = Facade.get_facade()
    
    @classmethod
    def add_mediator(cls, mediator):
        if mediator.NAME not in cls.__mediators:
            cls.__mediators[mediator.NAME] = mediator
            mediator.on_register()
        
    @classmethod
    def remove_mediator(cls, mediator):
        if mediator in cls.__mediators:
            mediator.on_unregister()
            cls.__mediators.pop(mediator.NAME)
    
    @classmethod
    def get_mediator(cls, name):
        return cls.__mediators[name]
        
    @classmethod
    def has_mediator(cls, name):
        return name in cls.__mediators

class Controller(Singleton):
    def __init__(self):
        Singleton.__init__(self)
        self.facade = Facade.get_facade()

class Facade(Singleton):
    model = None
    view = None
    controller = None
    
    __facade = None
    
    def __init__(self):
        Singleton.__init__(self)
        Facade.__facade = self
    
    @staticmethod
    def get_facade():
        return Facade.__facade
        
    def add_mediator    (self, *args, **kwargs): return  View().add_mediator   (*args, **kwargs)
    def remove_mediator (self, *args, **kwargs): return  View().remove_mediator(*args, **kwargs)
    def get_mediator    (self, *args, **kwargs): return  View().get_mediator   (*args, **kwargs)
    def has_mediator    (self, *args, **kwargs): return  View().has_mediator   (*args, **kwargs)
    def add_proxy       (self, *args, **kwargs): return Model().add_proxy      (*args, **kwargs)
    def remove_proxy    (self, *args, **kwargs): return Model().remove_proxy   (*args, **kwargs)
    def get_proxy       (self, *args, **kwargs): return Model().get_proxy      (*args, **kwargs)
    def has_proxy       (self, *args, **kwargs): return Model().has_proxy      (*args, **kwargs)
    
if __name__ == '__main__':
    # Test Singleton
    class A(Singleton): pass
    a = A()
    b = A()
    assert a is b, RuntimeError("Singleton class failed")
    assert A.get_instance() is A.get_instance()
