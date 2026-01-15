from typing import Optional, List, Any
from pydantic import BaseModel, Field


class EnumOptionBase(BaseModel):
    """Base enum option schema."""
    name: str = Field(..., min_length=1, max_length=255)
    color: Optional[str] = None
    enabled: bool = True


class EnumOptionCreate(EnumOptionBase):
    """Schema for creating an enum option."""
    insert_before: Optional[str] = None
    insert_after: Optional[str] = None


class EnumOptionUpdate(BaseModel):
    """Schema for updating an enum option."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = None
    enabled: Optional[bool] = None


class EnumOptionResponse(BaseModel):
    """Enum option response schema."""
    gid: str
    resource_type: str = "enum_option"
    name: str
    color: Optional[str] = None
    enabled: bool = True
    
    class Config:
        from_attributes = True


class CustomFieldBase(BaseModel):
    """Base custom field schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    resource_subtype: str = Field(default="text", pattern="^(text|enum|multi_enum|number|date|people)$")


class CustomFieldCreate(CustomFieldBase):
    """Schema for creating a custom field."""
    workspace: str = Field(..., description="Workspace GID")
    enum_options: Optional[List[EnumOptionCreate]] = None
    format: Optional[str] = Field(None, pattern="^(none|currency|percentage|custom)$")
    currency_code: Optional[str] = None
    custom_label: Optional[str] = None
    custom_label_position: Optional[str] = Field(None, pattern="^(prefix|suffix)$")
    precision: int = 0


class CustomFieldUpdate(BaseModel):
    """Schema for updating a custom field."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    format: Optional[str] = None
    currency_code: Optional[str] = None
    custom_label: Optional[str] = None
    precision: Optional[int] = None


class CustomFieldResponse(BaseModel):
    """Custom field response schema."""
    gid: str
    resource_type: str = "custom_field"
    resource_subtype: str = "text"
    name: str
    description: Optional[str] = None
    type: str = "text"
    enum_options: Optional[List[EnumOptionResponse]] = None
    format: Optional[str] = None
    currency_code: Optional[str] = None
    custom_label: Optional[str] = None
    custom_label_position: Optional[str] = None
    precision: int = 0
    is_formula_field: bool = False
    is_important: bool = False
    has_notifications_enabled: bool = False
    
    class Config:
        from_attributes = True


class CustomFieldCompact(BaseModel):
    """Compact custom field representation."""
    gid: str
    resource_type: str = "custom_field"
    name: str
    resource_subtype: str = "text"
    
    class Config:
        from_attributes = True


class CustomFieldSettingCreate(BaseModel):
    """Schema for adding a custom field to a project."""
    custom_field: str = Field(..., description="Custom field GID")
    is_important: bool = False
    insert_before: Optional[str] = None
    insert_after: Optional[str] = None


class CustomFieldSettingResponse(BaseModel):
    """Custom field setting response schema."""
    gid: str
    resource_type: str = "custom_field_setting"
    custom_field: dict
    project: dict
    is_important: bool = False
    
    class Config:
        from_attributes = True


class TaskCustomFieldValueUpdate(BaseModel):
    """Schema for updating a custom field value on a task."""
    text_value: Optional[str] = None
    number_value: Optional[float] = None
    date_value: Optional[str] = None
    enum_value: Optional[str] = None
    multi_enum_values: Optional[List[str]] = None
    people_value: Optional[List[str]] = None


