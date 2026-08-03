from __future__ import annotations

from typing import Any, Dict, List


statistics_minor_track_b_requirement: List[Dict[str, Any]] = [{'id': 'stat_minor_track_b_intro_statistics',
  'is_subrequirement': False,
  'requirement_type': 'choose_n',
  'courses': ['STAT 280', 'STAT 180', 'STAT 305'],
  'min_count': 1,
  'max_count': 1},
 {'id': 'stat_minor_track_b_data_methods',
  'is_subrequirement': False,
  'requirement_type': 'choose_n',
  'courses': ['STAT 385', 'DSCI 101'],
  'min_count': 1,
  'max_count': 1},
 {'id': 'stat_minor_track_b_electives',
  'is_subrequirement': False,
  'requirement_type': 'choose_n',
  'filters': {'subject': 'STAT', 'min_level': 300},
  'min_count': 4,
  'constraints': {'excluded_courses': ['STAT 305', 'STAT 385']}}]
