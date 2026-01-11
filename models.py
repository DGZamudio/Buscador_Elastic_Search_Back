from typing import List, Optional
from pydantic import BaseModel

class YearFilter(BaseModel):
    year_from : Optional[str] = None
    year_to   : Optional[str] = None
    
class ProximityFilter(BaseModel):
    distance : int = 8
    query    : Optional[str] = None

class SearchFilters(BaseModel):
    title         : Optional[str] = None
    proximity     : Optional[ProximityFilter] = None
    not_include   : Optional[List[str]] = None
    phrase        : Optional[str] = None
    document_type : Optional[str] = None
    must          : Optional[List[str]] = None
    should        : Optional[List[str]] = None
    years         : Optional[YearFilter] = None 
    entity        : Optional[str] = None
    
class SearchBody(BaseModel):
    skip    : int = 0
    limit   : int = 10
    filters : Optional[SearchFilters] = None
