from enum import Enum

from uiautomator2 import UiObjectNotFoundError

from module.logger import logger
from module.gg_handler.gg_data import GGData
from module.config.config import deep_get
from module.base.base import ModuleBase
import uiautomator2 as u2

class ShipData:
    def __init__(self, DataStr: str):
        DataList = DataStr.split(";")
        self.ShipId = DataList[0]
        self.Star = DataList[1]
        self.ShipType = DataList[2]
        self.TargetType = DataList[3]


class ChangeShip(ModuleBase):

    def __init__(self, config, device):
        super().__init__(config, device)
        self.d = u2.connect(self.device.serial)
        self.gg_package_name = deep_get(self.config.data, keys='GameManager.GGHandler.GGPackageName')

    def GetShipData(self):
        DataList = list()
        for i in deep_get(self.config.data, "GameManager.ChangeShip.ShipData").split("\n"):
            if i:
                DataList.append(ShipData(i))
        return DataList

    def PushLua(self):
        IsPush = deep_get(self.config.data, keys='GameManager.ChangeShip.PushLua')
        if IsPush:
            self.device.adb_shell("mkdir /sdcard/Notes")
            self.device.sleep(0.5)
            self.device.adb_shell("rm /sdcard/Notes/ShipChanger.lua")
            self.device.sleep(0.5)
            self.device.adb_push("bin/Lua/ShipChanger.lua", "/sdcard/Notes/ShipChanger.lua")
            self.device.sleep(0.5)
            logger.info('Lua Pushed')

    def ChangeShipType(self):
        if not deep_get(self.config.data, "GameManager.ChangeShip.Enable"):
            return 0
        HARDMODEMAPS = [
            'd1', 'd2', 'd3',
            'ht4', 'ht5', 'ht6',
        ]
        if not self.config.is_task_enabled("GemsFarming") or deep_get(self.config.data, "GemsFarming.Campaign.Name").lower() not in HARDMODEMAPS:
            return 0
        _set = False
        _confirmed = False
        while 1:
            if self.d(resourceId=f"{self.gg_package_name}:id/search_toolbar").exists:
                self.d.xpath(
                    f'//*[@resource-id="{self.gg_package_name}'
                    f':id/search_toolbar"]/android.widget.ImageView[last()]'
                ).click()
            self.device.sleep(1)
            if self.d(resourceId=f"{self.gg_package_name}:id/file").exists:
                self.d(resourceId=f"{self.gg_package_name}:id/file").send_keys("/sdcard/Notes/ShipChanger.lua")
                logger.info('Lua path set')
            if self.d.xpath('//*[@text="执行"]').exists:
                self.d.xpath('//*[@text="执行"]').click()
                logger.info('Click Run')
                self.device.sleep(0.5)
            if self.d.xpath('//*[contains(@text,"改船")]').exists:
                self.d.xpath('//*[contains(@text,"改船")]').click()
                logger.info('Click Change Statistic')
                self.device.sleep(0.5)
            if self.d(resourceId=f"{self.gg_package_name}:id/edit").exists:
                ShipDataList = self.GetShipData()
                ShipIdStr = ";".join([str(i.ShipId) for i in ShipDataList])
                ShipStarStr = ";".join([str(i.Star) for i in ShipDataList])
                CurrentShipTypeStr = ";".join([str(i.ShipType) for i in ShipDataList])
                TargetShipTypeStr = ";".join([str(i.TargetType) for i in ShipDataList])
                while 1:
                    try:
                        self.d(resourceId=f"{self.gg_package_name}:id/edit")[0].send_keys(ShipIdStr)
                        self.d(resourceId=f"{self.gg_package_name}:id/edit")[1].send_keys(ShipStarStr)
                        self.d(resourceId=f"{self.gg_package_name}:id/edit")[2].send_keys(CurrentShipTypeStr)
                        self.d(resourceId=f"{self.gg_package_name}:id/edit")[3].send_keys(TargetShipTypeStr)
                        break
                    except UiObjectNotFoundError:
                        self.d(className="android.widget.ScrollView")[0].scroll.toEnd()

                self.device.sleep(0.5)
                _set = True
            if _set and self.d.xpath('//*[@text="确定"]').exists:
                self.d.xpath('//*[@text="确定"]').click()
                logger.info("Click confirm")
                self.device.sleep(0.5)
                _confirmed = True
            self.d.wait_timeout = deep_get(self.config.data, "GameManager.ChangeShip.Timeout")

            if _set and _confirmed:
                try:
                    self.d.xpath('//*[@text="确定"]').click()
                    self.device.sleep(0.5)
                    self.d.xpath('//*[@text="确定"]').click()
                finally:
                    pass
            self.d.wait_timeout = 3
            if _set and _confirmed:
                break
            else:
                return 0

