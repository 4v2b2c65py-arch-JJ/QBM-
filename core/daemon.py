# QB Protocol Daemon Stub
from enum import Enum

class InstanceStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    PENDING = "pending"

class CoreType(Enum):
    CPU = "cpu"
    GPU = "gpu"
    NPU = "npu"

class Daemon:
    """Daemon stub for KRNL GPU system."""
    def __init__(self):
        self.running = False
        self.instances = {}
        self.cores = []
        self.node_id = "qb-protocol-node"
    
    def start(self):
        self.running = True
    
    def stop(self):
        self.running = False
    
    def register_instance(self, name, platform_name=None, metadata=None):
        inst_id = f"inst-{len(self.instances) + 1}"
        self.instances[inst_id] = type('Instance', (), {
            'instance_id': inst_id,
            'name': name,
            'status': InstanceStatus.PENDING.value,
            'platform': platform_name or 'unknown',
            'metadata': metadata or {}
        })()
        return self.instances[inst_id]
    
    def start_instance(self, instance_id):
        if instance_id in self.instances:
            self.instances[instance_id].status = InstanceStatus.RUNNING.value
            return True
        return False
    
    def stop_instance(self, instance_id):
        if instance_id in self.instances:
            self.instances[instance_id].status = InstanceStatus.STOPPED.value
            return True
        return False
    
    def register_core(self, instance_id, core_type, thread_id):
        core_id = f"core-{len(self.cores) + 1}"
        core = type('Core', (), {
            'core_id': core_id,
            'instance_id': instance_id,
            'core_type': core_type,
            'thread_id': thread_id,
            'load': 0.0,
            'temperature': 0.0
        })()
        self.cores.append(core)
        return core
    
    def update_core_heartbeat(self, core_id, load, temperature):
        for core in self.cores:
            if core.core_id == core_id:
                core.load = load
                core.temperature = temperature
                break
    
    def add_dream_layer(self, depth, projection, convergence, brain_state_emission, singularity_threshold):
        return {"depth": depth, "projection": projection, "convergence": convergence,
                "brain_state_emission": brain_state_emission, "singularity_threshold": singularity_threshold}
    
    def get_status(self):
        return {"node_id": self.node_id, "running": self.running,
                "instances": len(self.instances), "cores": len(self.cores)}
    
    def get_uptime(self):
        return 0
    
    def _save_state(self):
        pass

daemon = Daemon()
