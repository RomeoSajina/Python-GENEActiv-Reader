import math
import pandas as pd
import numpy as np
import struct
from bitstring import BitArray


class GENEActiv:

    def __init__(self, bin_file_path):
        """
        :param bin_file_path: full path to geneactiv .bin file
        """
        self.bin_file_path = bin_file_path
        self.raw = None
        self.data = None
        self.init()

    def init(self):
        self.raw = self.read()
        self.raw["SVM"] = self.raw.apply(lambda el: self.calc_svm(el["X"], el["Y"], el["Z"]), axis=1)
        self.data = self.raw.copy()[["SVM"]]

    def help(self):
        print("Check the manual for more info: https://www.activinsights.com/wp-content/uploads/2014/03/geneactiv_instruction_manual_v1.2.pdf, https://core.ac.uk/download/pdf/288378797.pdf")

    def read(self):
        """
        Reads geneactiv .bin files into a pandas dataframe
        :param bin_file_path: full path to geneactiv .bin file
        :return decode: pandas dataframe of GA data
        """

        with open(self.bin_file_path, "r") as in_file:

            full_line = in_file.readline()
            count = 0
            fs = ""
            df = []

            while full_line:
                full_line = in_file.readline()
                line = full_line[:].split("\n")[0]
                count += 1

                if count < 60:
                    if "x gain" in line:
                        x_gain = int(line.split(":")[-1])

                    if "x offset" in line:
                        x_offset = int(line.split(":")[-1])

                    if "y gain" in line:
                        y_gain = int(line.split(":")[-1])

                    if "y offset" in line:
                        y_offset = int(line.split(":")[-1])

                    if "z gain" in line:
                        z_gain = int(line.split(":")[-1])

                    if "z offset" in line:
                        z_offset = int(line.split(":")[-1])

                    if "Volts" in line:
                        volts = int(line.split(":")[-1])

                    if "Lux" in line:
                        lux = int(line.split(":")[-1])

                if "Page Time:" in line:
                    time = pd.to_datetime(
                        ":".join(line.split(":")[1:])[0:-2], format="%Y-%m-%d %H:%M:%S:%f"
                    )

                if "Temperature:" in line:
                    temp = float(line.split(":")[-1])

                if not fs:
                    if "Measurement Frequency:" in line:
                        fs = float(line.split(":")[-1].split(" ")[0])
                        offset = np.array([1 / fs] * 300) * np.arange(0, 300)
                        delta = pd.to_timedelta(offset, unit="s")

                if len(line) == 3600:
                    # hex to bin
                    hexes = struct.unpack("12s " * 300, line.encode("ascii"))
                    bins = (
                        struct.unpack(
                            "12s 12s 12s 10s 1s 1s", bytes(bin(int(hx, 16))[2:].zfill(48), "ascii")
                        )
                        for hx in hexes
                    )
                    decode = pd.DataFrame(
                        bins,
                        columns=["X", "Y", "Z", "LUX", "Button", "_"],
                        index=pd.DatetimeIndex([time] * 300) + delta,
                    )

                    # binary to decimal and calibration
                    decode.X = decode.X.apply(
                        lambda x: round(
                            (BitArray(bin=x.decode("ascii")).int * 100.0 - x_offset) / x_gain, 4
                        )
                    )
                    decode.Y = decode.Y.apply(
                        lambda x: round(
                            (BitArray(bin=x.decode("ascii")).int * 100.0 - y_offset) / y_gain, 4
                        )
                    )
                    decode.Z = decode.Z.apply(
                        lambda x: round(
                            (BitArray(bin=x.decode("ascii")).int * 100.0 - z_offset) / z_gain, 4
                        )
                    )
                    decode.LUX = decode.LUX.apply(lambda x: int(x, 2) * lux / volts)
                    decode["Temperature"] = temp
                    df.append(decode)

            df = pd.concat(df, axis=0)
            df.index.name = "Time"
            return df[["X", "Y", "Z", "LUX", "Temperature"]]

    @staticmethod
    def calc_svm(x, y, z):
        """
        alculate Signal Magnitude Vector (SVMgs) for x, y, z forces
        :return: svm value
        """
        return abs(math.sqrt(math.pow(x, 2) + math.pow(y, 2) + math.pow(z, 2)) - 1)

    def aggregate(self, freq="1s"):
        """
        aggregate the svm's over time
        :param freq: string defining grouping interval used by pandas Grouper: 1s, 10s, 60s, 1W, etc.
        :return: aggregated data
        """
        return self.data["SVM"].groupby(pd.Grouper(freq=freq)).sum().to_frame()
