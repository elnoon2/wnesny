# Use-case diagram

Use cases of the Wnesny service layer (`app/services/database_service.py`). The web pages that will call them are planned for M4.

```mermaid
flowchart LR
    M([Member])
    D([Driver])
    P([Passenger])
    D -. "is a member" .-> M
    P -. "is a member" .-> M

    subgraph System["Wnesny"]
        UC1(Register)
        UC2(Edit profile)
        UC3(Choose interests)
        UC4(Publish ride)
        UC5(Request to join a ride)
        UC6(Accept or reject a request)
        UC7(Start or complete ride)
        UC8(Cancel ride or request)
        UC9(Chat)
        UC10(Review the other person)
        UC11(Read notifications)
    end

    M --> UC1
    M --> UC2
    M --> UC3
    M --> UC11
    D --> UC4
    D --> UC6
    D --> UC7
    D --> UC8
    P --> UC5
    P --> UC8
    D --> UC9
    P --> UC9
    D --> UC10
    P --> UC10
```

Rules: only the driver accepts, rejects, starts, completes or cancels a ride; chat and reviews exist only for the accepted
passenger and the driver. See the table in [../architecture.md](../architecture.md).
