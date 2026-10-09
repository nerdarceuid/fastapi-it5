from pydantic import BaseModel, ConfigDict, Field

class CategoryInput(BaseModel):

    #extra="forbid" used if the users sends a field thats type or random then returns 422
    # the other one is self explanatory
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)

    description: str | None = Field(default=None, max_length=500)

#inherits categoryInput, this one will be sent back to the users
#Basically category as returned by the api
class Category(CategoryInput):

    #plain int, no rules. No clients should be able to send this field
    id: int

class EquipmentInput(BaseModel):
    """
    fields a user sends when for creating and updating

    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)

    category_id: int = Field(ge=1)

    description: str | None = Field(default=None, max_length=500)
    quantity_total: int = Field(ge=1, le=10000)

class Equipment(EquipmentInput):

    id: int
    category_name: str
    quantity_available: int