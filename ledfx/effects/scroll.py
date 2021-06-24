import numpy as np
import voluptuous as vol

from ledfx.color import COLORS
from ledfx.effects.audio import AudioReactiveEffect


class ScrollAudioEffect(AudioReactiveEffect):

    NAME = "Scroll"
    CATEGORY = "1.0"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "blur",
                description="Amount to blur the effect",
                default=3.0,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=10)),
            vol.Optional(
                "mirror",
                description="Mirror the effect",
                default=True,
            ): bool,
            vol.Optional(
                "speed", description="Speed of the effect", default=5
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
            vol.Optional(
                "decay",
                description="Decay rate of the scroll",
                default=0.97,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.8, max=1.0)),
            vol.Optional(
                "threshold",
                description="Cutoff for quiet sounds. Higher -> only loud sounds are detected",
                default=0.0,
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=1)),
            vol.Optional(
                "color_lows",
                description="Color of low, bassy sounds",
                default="red",
            ): vol.In(list(COLORS.keys())),
            vol.Optional(
                "color_mids",
                description="Color of midrange sounds",
                default="green",
            ): vol.In(list(COLORS.keys())),
            vol.Optional(
                "color_high",
                description="Color of high sounds",
                default="blue",
            ): vol.In(list(COLORS.keys())),
        }
    )

    def on_activate(self, pixel_count):
        self.output = np.zeros((pixel_count, 3))
        self.intensities = np.zeros(3)

    def config_updated(self, config):

        # TODO: Determine how buffers based on the pixels should be
        # allocated. Technically there is no guarantee that the effect
        # is bound to a device while the config gets updated. Might need
        # to move to a model where effects are created for a device and
        # must be destroyed and recreated to be moved to another device.
        self.lows_colour = np.array(
            COLORS[self._config["color_lows"]], dtype=float
        )
        self.mids_colour = np.array(
            COLORS[self._config["color_mids"]], dtype=float
        )
        self.high_colour = np.array(
            COLORS[self._config["color_high"]], dtype=float
        )

        self.lows_cutoff = self._config["threshold"]
        self.mids_cutoff = self._config["threshold"] / 4
        self.high_cutoff = self._config["threshold"] / 7

    def audio_data_updated(self, data):
        # Divide the melbank into lows, mids and highs
        self.intensities = np.fromiter(
            (i.max() ** 2 for i in self.melbank_thirds()), np.float
        )
        np.clip(self.intensities, 0, 1, out=self.intensities)

        if self.intensities[0] < self.lows_cutoff:
            self.intensities[0] = 0
        if self.intensities[1] < self.mids_cutoff:
            self.intensities[1] = 0
        if self.intensities[2] < self.high_cutoff:
            self.intensities[2] = 0

    def render(self):
        # Roll the effect and apply the decay
        speed = self.config["speed"]
        self.output[speed:, :] = self.output[:-speed, :]
        self.output = self.output * self.config["decay"]

        self.output[:speed] = self.lows_colour * self.intensities[0]
        self.output[:speed] += self.mids_colour * self.intensities[1]
        self.output[:speed] += self.high_colour * self.intensities[2]

        # Set the pixels
        return self.output
