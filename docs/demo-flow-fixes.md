# Correctifs du parcours démo (branche `flow`)

_Session des 06–08/11/2026. Contexte global : `infra-control/docs/demo-flow-fixes.md`._

## Résumé

| Branche (mergée en `--no-ff` dans `flow`) | Commit |
|---|---|
| `fix/discovery-power-state` | `fix: include power state and memory in the VM list` |

## `list_vm` : état d'alimentation et mémoire des VMs

- **Symptôme** : à la découverte VMware, toutes les VMs s'affichaient « Inconnu » côté UI.
- **Cause** : `vms_list_info` (`data_retriever/dto.py`) ne renvoyait ni `powerState` ni `memoryMB`, alors que le backend (`VmwareService.parseVmList`) et le front (`DiscoveredVmCard`) les lisent.
- **Correctif** : ajout de `powerState` (`vm.runtime.powerState`) et `memoryMB` (`vm.config.hardware.memoryMB`) à chaque VM.

## Compatibilité avec vcsim (pas de changement de code ici)

Pendant la session, `list_vm` plantait avec `AttributeError: summary` contre la stack démo. La cause n'est pas dans `ups_manager` : à partir de **vcsim v0.53.0**, le simulateur renvoie `runtime.faultToleranceState = ""` (enum vide) que **pyVmomi 9** refuse de désérialiser, si bien que tout accès à `vm.runtime` ou `vm.summary` lève une erreur. Le correctif est d'épingler vcsim en v0.52.0 dans `mock_vcsim` (testé : 0.48 et 0.52 OK, 0.53 → 0.56 KO). Un vrai vCenter n'est pas concerné.

## Tests

- `python -m unittest discover -s tests -t .` : 12 tests OK.
- Vérifié contre vcsim dans la stack démo : 20 VMs, `poweredOn`, 32 MB ; l'UI affiche « En ligne » et la RAM.
