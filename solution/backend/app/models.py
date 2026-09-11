
from sqlalchemy import Column, Integer, String, DateTime, Numeric
from app.database import Base

class Trade(Base):
    """
    SQLAlchemy модель для таблицы `trades` в базе данных.
    Представляет собой запись о торговой сделке с различными атрибутами.
    """
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True) # Уникальный идентификатор сделки, первичный ключ
    symbol = Column(String, index=True) # Торговый символ (например, BTCUSDT)
    strategy = Column(String, index=True) # Используемая торговая стратегия
    side = Column(String, index=True) # Тип сделки (long/short)
    opened_at = Column(DateTime(timezone=True)) # Время открытия сделки (UTC)
    closed_at = Column(DateTime(timezone=True), index=True) # Время закрытия сделки (UTC)
    qty = Column(Numeric(precision=18, scale=8)) # Количество актива
    entry_price = Column(Numeric(precision=18, scale=8)) # Цена входа в сделку
    exit_price = Column(Numeric(precision=18, scale=8)) # Цена выхода из сделки
    fee = Column(Numeric(precision=18, scale=8)) # Комиссия
    pnl = Column(Numeric(precision=18, scale=8), index=True) # Прибыль/убыток (PnL)

    def __repr__(self):
        return f"<Trade(id={self.id}, symbol='{self.symbol}', pnl={self.pnl})>"
