package com.mycompany.reconciliation;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import javax.sql.DataSource;

public class TransactionReconciler {

    private final DataSource dataSource;

    public TransactionReconciler(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    public int countOrphanedTransactions() throws SQLException {
        String sql = "SELECT COUNT(*) FROM transactions t " +
                     "LEFT JOIN customers c ON t.customer_id = c.customer_id " +
                     "WHERE c.customer_id IS NULL AND t.transaction_date = CURRENT_DATE";

        Connection conn = dataSource.getConnection();
        PreparedStatement stmt = conn.prepareStatement(sql);
        ResultSet rs = stmt.executeQuery();

        if (rs.next()) {
            return rs.getInt(1);
        }
        return 0;
    }
}