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

import pygame
import mvc
import model
import model.map
import view
import view.camera
import game
import os

class InitEvent(mvc.Event): pass
class IdleEvent(mvc.Event): pass
class QuitEvent(mvc.Event): pass
class MouseMotionEvent(mvc.Event): pass
class MouseButtonDownEvent(mvc.Event): pass
class MouseButtonUpEvent(mvc.Event): pass
class KeyDownEvent(mvc.Event): pass
class KeyUpEvent(mvc.Event): pass
class TickEvent(mvc.Event): pass

class PyGameController(mvc.Controller):
    tick_signal = TickEvent()
    init_signal = InitEvent()
    idle_signal = IdleEvent()
    quit_signal = QuitEvent()
    mousemotion_signal = MouseMotionEvent()
    mousebuttondown_signal = MouseButtonDownEvent()
    mousebuttonup_signal = MouseButtonUpEvent()
    keydown_signal = KeyDownEvent()
    keyup_signal = KeyUpEvent()

    signals_map = {
        pygame.QUIT: quit_signal,
        pygame.MOUSEMOTION: mousemotion_signal,
        pygame.MOUSEBUTTONDOWN: mousebuttondown_signal,
        pygame.MOUSEBUTTONUP: mousebuttonup_signal,
        pygame.KEYDOWN: keydown_signal,
        pygame.KEYUP: keyup_signal,
    }

    def start(self):
        opts = game.Game.options

        display = view.PyGameDisplay()
        display_mediator = view.PyGameDisplayMediator(display)

        # Install the view
        self.facade.add_mediator(display_mediator)

        # Install a new map
        map = model.map.Map()
        map_proxy = model.MapProxy(map)
        self.map_proxy = map_proxy
        self.facade.add_proxy(map_proxy)

        display_mediator.use_map(map_proxy)

        # Add a camera to view
        camera = view.camera.Camera()
        self.camera_mediator = view.camera.CameraMediator(camera)
        self.facade.add_mediator(self.camera_mediator)

        display_mediator.attach_camera(self.camera_mediator)

        # New main player
        player = model.MainPlayer('toto')
        player_proxy = model.PlayerProxy(player)
        self.facade.add_proxy(player_proxy)

        camera.set_player(player)
        map_proxy.add_player(player_proxy)

        # load level data using root game directory
        if opts.root is not None and os.path.isdir(opts.root):
            map.set_root(opts.root)

        # Signal that initialization is done
        self.init_signal.emit()

        # Build a default map state
        if game.Game.options.test:
            test = self.map_proxy.get_test_map(game.Game.options.test)
            if not test:
                raise SystemExit("test not found")
            test()
            map.do_occlusion()
            map.generate_faces()

        player.setup_on_level(map.player_data)
        self.update_map()

        # Run the event loop now
        display_mediator.run()

    def handler_input_events(self):
        # PyGame event parsing and dispatching (using Event signals)
        for event in pygame.event.get():
            self.signals_map.get(event.type, self.idle_signal).emit(event)

    def update_map(self):
        self.map_proxy.update()

    def start_game_mode(self):
        self.camera_mediator.enable()

    def stop_game_mode(self):
        self.camera_mediator.disable()

