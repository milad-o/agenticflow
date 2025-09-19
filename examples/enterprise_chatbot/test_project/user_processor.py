#!/usr/bin/env python3
"""
User Data Processing Module

This module processes user data from users.json and provides
analytics and reporting capabilities for the enterprise system.
"""

import json
import yaml
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from pathlib import Path

# Import configuration from config.yaml
from config_loader import load_config

# Setup logging based on config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class UserStats:
    """User statistics data class."""
    total_users: int
    active_users: int
    departments: List[str]
    average_salary: float
    skill_distribution: Dict[str, int]
    average_age: float

class UserProcessor:
    """
    Processes user data and generates insights.
    
    This class loads user data from users.json and provides
    various analytics and processing capabilities.
    """
    
    def __init__(self, data_file: str = "users.json", config_file: str = "config.yaml"):
        """Initialize the processor with data and config files."""
        self.data_file = Path(data_file)
        self.config_file = Path(config_file)
        self.users = []
        self.config = {}
        self.load_data()
        self.load_config()
    
    def load_data(self) -> None:
        """Load user data from JSON file."""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.users = data.get('users', [])
                self.metadata = data.get('metadata', {})
            logger.info(f"Loaded {len(self.users)} users from {self.data_file}")
        except FileNotFoundError:
            logger.error(f"Data file {self.data_file} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.data_file}: {e}")
            raise
    
    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self.config_file}")
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_file} not found, using defaults")
            self.config = {}
    
    def get_user_stats(self) -> UserStats:
        """Calculate comprehensive user statistics."""
        if not self.users:
            return UserStats(0, 0, [], 0.0, {}, 0.0)
        
        active_users = len([u for u in self.users if u.get('active', True)])
        departments = list(set(u.get('department', 'Unknown') for u in self.users))
        total_salary = sum(u.get('salary', 0) for u in self.users)
        average_salary = total_salary / len(self.users) if self.users else 0
        
        # Calculate skill distribution
        skill_dist = {}
        for user in self.users:
            for skill in user.get('skills', []):
                skill_dist[skill] = skill_dist.get(skill, 0) + 1
        
        # Calculate average age
        total_age = sum(u.get('age', 0) for u in self.users)
        average_age = total_age / len(self.users) if self.users else 0
        
        return UserStats(
            total_users=len(self.users),
            active_users=active_users,
            departments=sorted(departments),
            average_salary=average_salary,
            skill_distribution=skill_dist,
            average_age=average_age
        )
    
    def get_users_by_department(self, department: str) -> List[Dict[str, Any]]:
        """Get all users in a specific department."""
        return [u for u in self.users if u.get('department', '').lower() == department.lower()]
    
    def get_users_by_skill(self, skill: str) -> List[Dict[str, Any]]:
        """Get all users with a specific skill."""
        return [u for u in self.users 
                if skill.lower() in [s.lower() for s in u.get('skills', [])]]
    
    def export_to_csv(self, output_file: str = "users_export.csv") -> str:
        """Export user data to CSV format."""
        import csv
        
        if not self.users:
            return "No users to export"
        
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['id', 'name', 'email', 'age', 'department', 'skills', 'salary', 'active']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for user in self.users:
                writer.writerow({
                    'id': user.get('id'),
                    'name': user.get('name'),
                    'email': user.get('email'),
                    'age': user.get('age'),
                    'department': user.get('department'),
                    'skills': ', '.join(user.get('skills', [])),
                    'salary': user.get('salary'),
                    'active': user.get('active', True)
                })
        
        return f"Successfully exported {len(self.users)} users to {output_file}"
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive user report."""
        stats = self.get_user_stats()
        
        # Find top skills
        top_skills = sorted(stats.skill_distribution.items(), 
                          key=lambda x: x[1], reverse=True)[:5]
        
        # Department breakdown
        dept_breakdown = {}
        for dept in stats.departments:
            dept_users = self.get_users_by_department(dept)
            dept_breakdown[dept] = {
                'count': len(dept_users),
                'average_salary': sum(u.get('salary', 0) for u in dept_users) / len(dept_users) if dept_users else 0,
                'skills': list(set(skill for u in dept_users for skill in u.get('skills', [])))
            }
        
        return {
            'report_generated': datetime.now().isoformat(),
            'total_statistics': {
                'total_users': stats.total_users,
                'active_users': stats.active_users,
                'average_salary': stats.average_salary,
                'average_age': stats.average_age
            },
            'top_skills': top_skills,
            'department_breakdown': dept_breakdown,
            'configuration_version': self.config.get('application', {}).get('version', 'unknown')
        }

def main():
    """Main function to demonstrate user processing."""
    processor = UserProcessor()
    
    # Generate statistics
    stats = processor.get_user_stats()
    print(f"User Statistics: {stats}")
    
    # Generate report
    report = processor.generate_report()
    print(f"Report: {json.dumps(report, indent=2)}")
    
    # Export to CSV
    result = processor.export_to_csv()
    print(result)

if __name__ == "__main__":
    main()