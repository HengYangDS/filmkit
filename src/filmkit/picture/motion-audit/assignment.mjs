/* The assignment of least total cost between two sets, by which the motion audit follows a group of like marks from one
 * frame to the next. */

/** For a square matrix of costs, the column each row is assigned so that the sum of their costs is least: the
 * Hungarian method with potentials (Kuhn and Munkres), in O(n³). */
export function leastCostAssignment(cost) {
  const n = cost.length,
    u = new Float64Array(n + 1),
    v = new Float64Array(n + 1),
    rowOfColumn = new Int32Array(n + 1),
    way = new Int32Array(n + 1);
  for (let row = 1; row <= n; row++) {
    rowOfColumn[0] = row;
    let column = 0;
    const least = new Float64Array(n + 1).fill(Infinity),
      seen = new Uint8Array(n + 1);
    do {
      seen[column] = 1;
      const current = rowOfColumn[column];
      let delta = Infinity,
        next = 0;
      for (let j = 1; j <= n; j++) {
        if (seen[j]) continue;
        const reduced = cost[current - 1][j - 1] - u[current] - v[j];
        if (reduced < least[j]) {
          least[j] = reduced;
          way[j] = column;
        }
        if (least[j] < delta) {
          delta = least[j];
          next = j;
        }
      }
      for (let j = 0; j <= n; j++) {
        if (seen[j]) {
          u[rowOfColumn[j]] += delta;
          v[j] -= delta;
        } else least[j] -= delta;
      }
      column = next;
    } while (rowOfColumn[column] !== 0);
    do {
      const previous = way[column];
      rowOfColumn[column] = rowOfColumn[previous];
      column = previous;
    } while (column);
  }
  const columnOfRow = new Int32Array(n).fill(-1);
  for (let j = 1; j <= n; j++) if (rowOfColumn[j]) columnOfRow[rowOfColumn[j] - 1] = j - 1;
  return columnOfRow;
}
