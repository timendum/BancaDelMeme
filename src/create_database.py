from sqlalchemy import create_engine

import config
import models


def main():
    print("Creating the engine...")
    engine = create_engine(config.DB)
    models.Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
