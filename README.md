
```mermaid
classDiagram
    Voo: int id 
    Voo: int numero_voo
    Voo: int cia
    Voo: str origem
    Voo: str destino
    Voo: str status
    Voo: datetime horario_partida
    Voo: datetime horario_chegada
    Voo: int id_aeronave
    
    Aeronave: int id 
    Aeronave: String modelo
    Aeronave: datetime last_check
    Aeronave: datetime next_check

    Cia: int id
    Cia: String nome 
    Cia: String cod_iata

    Aeronave "*" -- "*" Cia
    Cia "*" -- "1" Voo
    Voo "*" -- "1" Aeronave

```mermaid