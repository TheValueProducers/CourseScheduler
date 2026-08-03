from __future__ import annotations

from typing import Any, Dict, List


statistics_minor_track_a_requirement: List[Dict[str, Any]] = [{'id': 'stat_minor_track_a_probability_statistics',
  'is_subrequirement': False,
  'requirement_type': 'choose_n',
  'courses': ['STAT 310', 'ECON 307', 'STAT 311', 'STAT 315', 'DSCI 301'],
  'min_count': 1,
  'max_count': 1},
 {'id': 'stat_minor_track_a_statistical_computation',
  'is_subrequirement': False,
  'requirement_type': 'required_courses',
  'courses': ['STAT 405'],
  'min_count': 1,
  'max_count': 1},
 {'id': 'stat_minor_track_a_linear_regression',
  'is_subrequirement': False,
  'requirement_type': 'required_courses',
  'courses': ['STAT 410'],
  'min_count': 1,
  'max_count': 1},
 {'id': 'stat_minor_track_a_electives',
  'is_subrequirement': False,
  'requirement_type': 'choose_n',
  'filters': {'subject': 'STAT', 'min_level': 300},
  'min_count': 3,
  'constraints': {'excluded_courses': ['STAT 305',
                                       'STAT 310',
                                       'STAT 311',
                                       'STAT 315',
                                       'STAT 385']}}]
