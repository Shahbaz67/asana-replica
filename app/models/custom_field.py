from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.project import Project
    from app.models.task import Task


class CustomField(AsanaBase):
    """Custom field definition."""
    __tablename__ = "custom_fields"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Resource subtype (text, enum, multi_enum, number, date, people)
    resource_subtype: Mapped[str] = mapped_column(String(50), default="text", nullable=False)
    
    # Type (deprecated, same as resource_subtype)
    type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)
    
    # Format for number fields (none, currency, percentage, custom)
    format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Currency code for currency format
    currency_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Custom label for number fields
    custom_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    custom_label_position: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Precision for number fields
    precision: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Is formula field
    is_formula_field: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Is important field (shown prominently)
    is_important: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Has notifications enabled
    has_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Date value uses time
    date_value_has_time: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Foreign keys
    workspace_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("workspaces.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Created by user
    created_by_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="custom_fields")
    
    enum_options: Mapped[List["CustomFieldEnumOption"]] = relationship(
        "CustomFieldEnumOption",
        back_populates="custom_field",
        cascade="all, delete-orphan",
        order_by="CustomFieldEnumOption.order",
    )
    
    settings: Mapped[List["CustomFieldSetting"]] = relationship(
        "CustomFieldSetting",
        back_populates="custom_field",
        cascade="all, delete-orphan",
    )
    
    @property
    def resource_type(self) -> str:
        return "custom_field"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "resource_subtype": self.resource_subtype,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "is_formula_field": self.is_formula_field,
            "is_important": self.is_important,
            "has_notifications_enabled": self.has_notifications_enabled,
        }
        
        if self.resource_subtype == "number":
            response["format"] = self.format
            response["precision"] = self.precision
            if self.currency_code:
                response["currency_code"] = self.currency_code
            if self.custom_label:
                response["custom_label"] = self.custom_label
                response["custom_label_position"] = self.custom_label_position
                
        return response


class CustomFieldEnumOption(AsanaBase):
    """Enum option for custom fields."""
    __tablename__ = "custom_field_enum_options"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Foreign keys
    custom_field_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("custom_fields.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    custom_field: Mapped["CustomField"] = relationship("CustomField", back_populates="enum_options")
    
    @property
    def resource_type(self) -> str:
        return "enum_option"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "color": self.color,
            "enabled": self.enabled,
        }


class CustomFieldSetting(AsanaBase):
    """Custom field setting - associates custom fields with projects."""
    __tablename__ = "custom_field_settings"
    
    is_important: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Foreign keys
    custom_field_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("custom_fields.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("projects.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    custom_field: Mapped["CustomField"] = relationship("CustomField", back_populates="settings")
    project: Mapped["Project"] = relationship("Project", back_populates="custom_field_settings")
    
    @property
    def resource_type(self) -> str:
        return "custom_field_setting"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "custom_field": {"gid": self.custom_field_gid, "resource_type": "custom_field"},
            "project": {"gid": self.project_gid, "resource_type": "project"},
            "is_important": self.is_important,
        }


class TaskCustomFieldValue(AsanaBase):
    """Value of a custom field on a task."""
    __tablename__ = "task_custom_field_values"
    
    # Text value
    text_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Number value
    number_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Date value
    date_value: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Display value (computed)
    display_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Foreign keys
    task_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("tasks.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    custom_field_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("custom_fields.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Enum value (for enum fields)
    enum_value_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("custom_field_enum_options.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Multi-enum values stored as comma-separated GIDs
    multi_enum_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # People values stored as comma-separated user GIDs
    people_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="custom_field_values")
    custom_field: Mapped["CustomField"] = relationship("CustomField")
    enum_value: Mapped[Optional["CustomFieldEnumOption"]] = relationship("CustomFieldEnumOption")
    
    @property
    def resource_type(self) -> str:
        return "custom_field_value"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.custom_field_gid,  # Use custom field GID
            "resource_type": "custom_field",
        }
        
        if self.text_value is not None:
            response["text_value"] = self.text_value
        if self.number_value is not None:
            response["number_value"] = self.number_value
        if self.date_value is not None:
            response["date_value"] = self.date_value
        if self.display_value is not None:
            response["display_value"] = self.display_value
        if self.enum_value_gid:
            response["enum_value"] = {"gid": self.enum_value_gid, "resource_type": "enum_option"}
        if self.multi_enum_values:
            gids = self.multi_enum_values.split(",")
            response["multi_enum_values"] = [{"gid": gid, "resource_type": "enum_option"} for gid in gids if gid]
        if self.people_values:
            gids = self.people_values.split(",")
            response["people_value"] = [{"gid": gid, "resource_type": "user"} for gid in gids if gid]
            
        return response


