"""
System information feature for voice assistant.
Provides CPU, memory, disk usage, and system stats.
"""
import psutil
import platform
import logging

logger = logging.getLogger(__name__)


class SystemInfo:
    """Provides system information and stats."""

    def __init__(self):
        """Initialize system info provider."""
        pass

    def _is_system_query(self, query: str) -> bool:
        """
        Check if query is asking about system info.
        
        Args:
            query: User's query
            
        Returns:
            True if query is about system info
        """
        query_lower = query.lower()
        
        system_keywords = [
            'cpu', 'processor', 'memory', 'ram',
            'disk', 'storage', 'space', 'system',
            'battery', 'performance', 'usage'
        ]
        
        return any(keyword in query_lower for keyword in system_keywords)

    def get_system_info(self, query: str) -> str:
        """
        Process system info query and return stats.
        
        Args:
            query: User's query
            
        Returns:
            System information as string
        """
        if not self._is_system_query(query):
            return None
        
        query_lower = query.lower()
        
        try:
            # CPU usage
            if 'cpu' in query_lower or 'processor' in query_lower:
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count()
                return f"CPU usage is {cpu_percent}% across {cpu_count} cores"
            
            # Memory usage
            elif 'memory' in query_lower or 'ram' in query_lower:
                mem = psutil.virtual_memory()
                used_gb = mem.used / (1024**3)
                total_gb = mem.total / (1024**3)
                return f"Memory usage is {mem.percent}%. Using {used_gb:.1f} GB out of {total_gb:.1f} GB"
            
            # Disk usage
            elif 'disk' in query_lower or 'storage' in query_lower or 'space' in query_lower:
                disk = psutil.disk_usage('/')
                used_gb = disk.used / (1024**3)
                total_gb = disk.total / (1024**3)
                free_gb = disk.free / (1024**3)
                return f"Disk usage is {disk.percent}%. {free_gb:.1f} GB free out of {total_gb:.1f} GB total"
            
            # Battery (if laptop)
            elif 'battery' in query_lower:
                battery = psutil.sensors_battery()
                if battery:
                    plugged = "plugged in" if battery.power_plugged else "on battery"
                    return f"Battery is at {battery.percent}%, {plugged}"
                else:
                    return "No battery detected. This might be a desktop system"
            
            # General system info
            else:
                cpu_percent = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                info = (
                    f"System status: CPU at {cpu_percent}%, "
                    f"memory at {mem.percent}%, "
                    f"disk at {disk.percent}%"
                )
                return info
        
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return "Sorry, I couldn't get system information"
