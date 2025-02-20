from catasta import Archway
from pydantic import BaseModel


def main() -> None:
    archway = Archway("models/transformer.onnx")

    class Input(BaseModel):
        s0: float
        s1: float
        s2: float
        s3: float

    archway.serve(
        host="145.94.123.92",
        port=8080,
        pydantic_model=Input,
    )


if __name__ == "__main__":
    main()
