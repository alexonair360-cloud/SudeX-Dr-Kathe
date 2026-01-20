from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from bson import ObjectId
from pydantic_core import CoreSchema, core_schema
from pydantic.json_schema import JsonSchemaValue

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ]),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v: Any) -> ObjectId:
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: CoreSchema, handler: Any
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class UserResponse(UserBase):
    id: str

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class TTSSettings(BaseModel):
    language: str
    persona: str
    speed: float
    pitch: int
    style_instruction: Optional[str] = None
    voice_style: Optional[str] = "Neutral"  # For Bhashini: Neutral, Book, Conversational, etc.
    is_premium: bool = False

class TTSSegment(BaseModel):
    text: str
    persona: str
    language: str
    speed: float
    pitch: int
    style_instruction: Optional[str] = None
    voice_style: Optional[str] = "Neutral"  # For Bhashini: Neutral, Book, Conversational, etc.

class TTSRequest(BaseModel):
    text: Optional[str] = None
    settings: Optional[TTSSettings] = None
    segments: Optional[List[TTSSegment]] = None
    title: Optional[str] = None
    is_premium: bool = False

class TTSHistory(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    title: Optional[str] = None
    text: str
    settings: TTSSettings
    audio_path: str
    is_public: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class PublicStory(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    original_history_id: str
    user_id: str
    title: Optional[str] = None
    text: str
    settings: TTSSettings
    audio_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
