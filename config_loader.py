import os
import json
import yaml
from typing import Dict, Any

class ConfigLoader:
    @staticmethod
    def load(file_path: str) -> Dict[str, Any]:
        """
        加载配置文件
        :param file_path: 配置文件路径
        :return: 配置字典
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"配置文件 {file_path} 不存在")

        _, ext = os.path.splitext(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            if ext.lower() in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            elif ext.lower() == '.json':
                config = json.load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {ext}")

        # 加前缀：image/
        ConfigLoader._apply_default_image_path(config)

        return config
        
    @staticmethod
    def validate(config: Dict[str, Any]):
        """配置校验"""
        required_fields = ['adb_path', 'steps', 'adb_ip']
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"缺少必要配置项: {field}")

        for i, step in enumerate(config['steps']):
            if 'targets' not in step:
                raise ValueError(f"步骤 {i+1} 缺少 targets 配置")
                
    @staticmethod
    def _apply_default_image_path(config: Dict[str, Any], base_dir: str = "image"):
        def prepend_path(path):
            if path and not os.path.isabs(path) and not path.startswith(base_dir):
                return os.path.join(base_dir, path)
            return path

        # 主 steps
        for step in config.get('steps', []):
            for target in step.get('targets', []):
                target['path'] = prepend_path(target.get('path'))
            if 'loop_until_target' in step:
                step['loop_until_target'] = prepend_path(step.get('loop_until_target'))

        # 辅助 steps
        for helper in config.get('helper_steps', {}).values():
            if 'trigger_image' in helper:
                helper['trigger_image'] = prepend_path(helper.get('trigger_image'))

        # 循环退出条件
        if 'loop' in config and 'exit_condition' in config['loop']:
            config['loop']['exit_condition']['target'] = prepend_path(
                config['loop']['exit_condition'].get('target')
            )
            
        # 全局监听子循环
        if 'global_monitor' in config:
            # 处理 trigger_image
            trigger_image = config['global_monitor'].get('trigger_image')
            if trigger_image:
                config['global_monitor']['trigger_image'] = prepend_path(trigger_image)

            # 处理子循环的步骤和退出条件
            target_loop = config['global_monitor'].get('target_loop', {})
            # 1. 处理步骤中的 targets
            for step in target_loop.get('steps', []):
                for target in step.get('targets', []):
                    target['path'] = prepend_path(target.get('path'))
                if 'loop_until_target' in step:
                    step['loop_until_target'] = prepend_path(step.get('loop_until_target'))
            # 2. 处理子循环的退出条件
            if 'exit_condition' in target_loop:
                exit_target = target_loop['exit_condition'].get('target')
                if exit_target:
                    target_loop['exit_condition']['target'] = prepend_path(exit_target)