from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()



from sqlalchemy import Boolean

class AppUser(Base):
    __tablename__ = "app_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    password = Column(String(255))
    is_admin = Column(Boolean, default=False)



class DimUser(Base):
    __tablename__ = "dim_user"

    user_id = Column(Integer, primary_key=True, index=True)

   
    user_code = Column(String(50), unique=True, nullable=False)

    name = Column(String(100), nullable=True)
    email = Column(String(150), nullable=True)
    risk_profile = Column(String(50), nullable=True)

    transactions = relationship("FactTransaction", back_populates="user")


class DimPaymentGateway(Base):
    __tablename__ = "dim_payment_gateway"

    gateway_id = Column(Integer, primary_key=True)
    gateway_name = Column(String(100))
    provider = Column(String(100))
    country = Column(String(50))

    transactions = relationship("FactTransaction", back_populates="gateway")



class DimRuleEngine(Base):
    __tablename__ = "dim_rule_engine"

    rule_id = Column(Integer, primary_key=True)
    rule_name = Column(String(100))
    severity = Column(String(50))
    threshold = Column(Numeric)

    transactions = relationship("FactTransaction", back_populates="rule")



class DimMLModel(Base):
    __tablename__ = "dim_ml_model"

    ml_model_id = Column(Integer, primary_key=True)
    model_name = Column(String(100))
    algorithm = Column(String(100))
    version = Column(String(50))

    transactions = relationship("FactTransaction", back_populates="ml_model")


class DimWebhook(Base):
    __tablename__ = "dim_webhook"

    webhook_id = Column(Integer, primary_key=True)
    event_type = Column(String(100))
    delivery_status = Column(String(50))
    retry_count = Column(Integer)

    transactions = relationship("FactTransaction", back_populates="webhook")




class DimTime(Base):
    __tablename__ = "dim_time"

    time_id = Column(Integer, primary_key=True)
    date = Column(String(20))
    month = Column(Integer)
    year = Column(Integer)
    hour = Column(Integer)

    transactions = relationship("FactTransaction", back_populates="time")




class FactTransaction(Base):
    __tablename__ = "fact_transaction"

    transaction_id = Column(String(100), primary_key=True)

    user_id = Column(Integer, ForeignKey("dim_user.user_id"))
    gateway_id = Column(Integer, ForeignKey("dim_payment_gateway.gateway_id"))
    rule_id = Column(Integer, ForeignKey("dim_rule_engine.rule_id"))
    ml_model_id = Column(Integer, ForeignKey("dim_ml_model.ml_model_id"))
    webhook_id = Column(Integer, ForeignKey("dim_webhook.webhook_id"))
    time_id = Column(Integer, ForeignKey("dim_time.time_id"))

    amount = Column(Numeric)
    fraud_score = Column(Numeric)
    final_decision = Column(String(50))

    user = relationship("DimUser", back_populates="transactions")
    gateway = relationship("DimPaymentGateway", back_populates="transactions")
    rule = relationship("DimRuleEngine", back_populates="transactions")
    ml_model = relationship("DimMLModel", back_populates="transactions")
    webhook = relationship("DimWebhook", back_populates="transactions")
    time = relationship("DimTime", back_populates="transactions")
    latency_ms = Column(Integer)

